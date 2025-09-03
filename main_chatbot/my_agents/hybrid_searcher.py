# hybrid search (latest-only retrieve)
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import os
import logging
from types import SimpleNamespace

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

from state_schema import AgentState, RetrievalHit

# -----------------------------------------------------------------------------
# Environment & Constants
# -----------------------------------------------------------------------------

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEBUG: bool = True

QDRANT_URL: Optional[str] = os.getenv("QDRANT_URL")
QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "dental_chunks"
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


DENSE_MODEL = "intfloat/multilingual-e5-large"
SPARSE_MODEL = "prithivida/Splade_PP_en_v1"

# Default limits
DEFAULT_LIMIT = 10
PREFETCH_MIN = 50  # max(50, limit)

# Logging
logger = logging.getLogger(__name__)
if DEBUG:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

# -----------------------------------------------------------------------------
# Module-level client cache
# -----------------------------------------------------------------------------

_qdrant_client: Optional[QdrantClient] = None


def set_qdrant_client(client: QdrantClient) -> None:
    global _qdrant_client
    _qdrant_client = client


def _get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return _qdrant_client

# -----------------------------------------------------------------------------
# Utilities: state-safe accessors & (legacy) query builder
# -----------------------------------------------------------------------------

def _latest_text(state: AgentState) -> str:
    """Safely read the latest user query text from state."""
    return (
        getattr(state, "user_query_latest", None)
        or getattr(state, "user_query", "")
        or ""
    )

# -----------------------------------------------------------------------------
# Core: Hybrid Search over Qdrant
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class HybridSearchParams:
    collection: str = COLLECTION_NAME
    limit: int = DEFAULT_LIMIT
    dedupe_mode: str = "per_chunk"  # "per_chunk" or "per_point"


def _prefetch_list(qtext: str, per_branch_limit: int) -> List[models.Prefetch]:
    """Construct prefetch list for dense and sparse branches."""
    return [
        models.Prefetch(
            query=models.Document(text=qtext, model=DENSE_MODEL),
            using=DENSE_VECTOR_NAME,
            limit=per_branch_limit,
        ),
        models.Prefetch(
            query=models.Document(text=qtext, model=SPARSE_MODEL),
            using=SPARSE_VECTOR_NAME,
            limit=per_branch_limit,
        ),
    ]


def _qdrant_query(
    client: QdrantClient,
    collection: str,
    qtext: str,
    qfilter: Optional[models.Filter],
    out_limit: int,
) -> List[Dict]:
    """Execute one hybrid (RRF) query round with an optional pre-filter.

    Returns a list of dicts: {"id": ..., "score": ..., "payload": ...}
    """
    per_branch = max(PREFETCH_MIN, out_limit)

    if DEBUG:
        logger.info("[qdrant][QTEXT]\n%s", qtext)
        logger.info("[qdrant][QUERY] %s", {"limit": out_limit, "has_filter": qfilter is not None})
        if qfilter is not None:
            try:
                logger.info("[qdrant][FILTER] %s", qfilter.dict())
            except Exception:
                logger.info("[qdrant][FILTER](repr) %r", qfilter)

    try:
        resp = client.query_points(
            collection_name=collection,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            prefetch=_prefetch_list(qtext, per_branch),
            query_filter=qfilter,
            limit=out_limit,
        )
        points = resp.points
    except Exception as exc:
        if DEBUG:
            logger.exception("[qdrant][ERROR] %r", exc)
        return []

    out = [{"id": p.id, "score": p.score, "payload": p.payload} for p in points]
    if DEBUG:
        for x in out[:5]:
            md = x.get("payload") or {}
            logger.info(
                "[qdrant][HIT] %s %.3f | cat_keys=%s | l1=%s | l2=%s",
                x["id"],
                x["score"],
                md.get("cat_keys"),
                md.get("category_level_1"),
                md.get("category_level_2"),
            )
    return out


def _dedupe(hits: Iterable[Dict], mode: str) -> List[Dict]:
    """Dedupe hits by chunk_id (per_chunk) or by point id (per_point)."""
    mode = mode if mode in ("per_chunk", "per_point") else "per_chunk"
    seen: set = set()
    uniq: List[Dict] = []

    for h in hits:
        p = h.get("payload") or {}
        key = p.get("chunk_id") if mode == "per_chunk" else h.get("id")
        if not key or key in seen:
            continue
        uniq.append(h)
        seen.add(key)
    return uniq


def _as_list(v) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


def _boost_score(h: Dict, cat_keys: Sequence[str], category_level_1: Sequence[str]) -> float:
    """Compute boosted score: base + 0.2 if cat_keys match; +0.1 if L1 match."""
    p = h.get("payload") or {}
    base = float(h.get("score", 0.0) or 0.0)

    b = 0.0
    if cat_keys:
        hit_cats = _as_list(p.get("cat_keys"))
        if any(k in hit_cats for k in cat_keys):
            b += 0.2

    if category_level_1:
        hit_l1 = _as_list(p.get("category_level_1"))
        if any(l1 in hit_l1 for l1 in category_level_1):
            b += 0.1

    return base + b


def hybrid_search_qdrant(
    client: QdrantClient,
    collection: str,
    text: str,
    cat_keys: Optional[List[str]] = None,
    category_level_1: Optional[List[str]] = None,
    limit: int = DEFAULT_LIMIT,
    dedupe_mode: str = "per_chunk",
) -> List[Dict]:
    """Perform pre-filtered hybrid search (dense + sparse with RRF) against Qdrant.

    Strategy:
      1) Round #1: exact cat_keys pre-filter (if provided)
      2) Round #2: category_level_1 pre-filter (if Round #1 insufficient)
      3) Round #3: no filter (if still need more)
      4) Dedupe, then apply small category-based boosts, sort & truncate to `limit`.
    """
    # ใช้ latest-only text ตรง ๆ (ตัด prefix "query:" ออก)
    qtext = text.strip() if text else ""

    # sanitize filters (preserve order but unique)
    cat_keys = list(dict.fromkeys(cat_keys or []))
    category_level_1 = list(dict.fromkeys(category_level_1 or []))

    # Round 1: exact cat_keys
    hits_exact: List[Dict] = []
    if cat_keys:
        f_exact = models.Filter(
            must=[models.FieldCondition(key="cat_keys", match=models.MatchAny(any=cat_keys))]
        )
        hits_exact = _qdrant_query(client, collection, qtext, f_exact, limit)

    # Round 2: fallback by L1 (category_level_1)
    hits_l1: List[Dict] = []
    if category_level_1 and len(hits_exact) < max(1, limit // 2):
        f_l1 = models.Filter(
            must=[models.FieldCondition(key="category_level_1", match=models.MatchAny(any=category_level_1))]
        )
        hits_l1 = _qdrant_query(client, collection, qtext, f_l1, limit)

    # Round 3: no filter
    need_more = max(0, limit - len(hits_exact) - len(hits_l1))
    hits_any: List[Dict] = _qdrant_query(client, collection, qtext, None, need_more) if need_more else []

    # Merge & dedupe
    merged = hits_exact + hits_l1 + hits_any
    uniq = _dedupe(merged, dedupe_mode)

    # Boost & sort
    uniq.sort(key=lambda h: _boost_score(h, cat_keys, category_level_1), reverse=True)
    return uniq[:limit]

# -----------------------------------------------------------------------------
# Helpers: Bucketing, Fallback & State update
# -----------------------------------------------------------------------------

def _bucketize_any(hits: Sequence[Dict], bucket_key: str = "ทั่วไป") -> Dict[str, List[RetrievalHit]]:
    """Convert raw Qdrant hits into RetrievalHit objects under a single bucket key."""
    bucket: List[RetrievalHit] = []
    for h in hits or []:
        p = h.get("payload") or {}
        snip = p.get("text", "")
        cid = p.get("chunk_id") or (str(h.get("id")) if h.get("id") is not None else "")
        if not cid:
            continue
        bucket.append(
            RetrievalHit(
                chunk_id=cid,
                score=float(h.get("score", 0.0) or 0.0),
                snippets=[snip] if snip else [],
                metadata={k: v for k, v in p.items() if k not in ("text", "doc_id")},
            )
        )
    return {bucket_key: bucket} if bucket else {}


def _set_hits_by_category(state: AgentState, hb: Dict[str, List[RetrievalHit]]) -> None:
    """Safely update state.retrieval_result.hits_by_category even if retrieval_result is None."""
    rr = getattr(state, "retrieval_result", None)
    try:
        if rr is not None and hasattr(rr, "model_copy"):
            state.retrieval_result = rr.model_copy(update={"hits_by_category": hb})
        else:
            state.retrieval_result = SimpleNamespace(hits_by_category=hb)
    except Exception:
        state.retrieval_result = SimpleNamespace(hits_by_category=hb)

# -----------------------------------------------------------------------------
# Orchestrator: Node entrypoint used by the agent pipeline
# -----------------------------------------------------------------------------

def hybrid_search_node(state: AgentState) -> AgentState:
    """Agent node:
       - No categories → search(no filter) → hits? → General / clarify
       - With categories → search(filters: exact→L1→none) → hits?
         → match wanted cats? → exact buckets / General / clarify
    """
    logger.info("[hybrid_search] เริ่มค้นหา")

    cats = getattr(state, "classification_result", None)
    cats = getattr(cats, "categories", []) if cats else []

    # ---- ใช้ 'ข้อความผู้ใช้รอบนี้' (latest-only) เป็นคิวรี ----
    qtext = _latest_text(state).strip()
    if not qtext:
        state.response = "ยังไม่ได้รับคำถามล่าสุดค่ะ รบกวนพิมพ์คำถามอีกครั้งนะคะ"
        return state

    # A) ไม่มีหมวดจาก classifier → search without filter
    if not cats:
        try:
            hits = hybrid_search_qdrant(
                client=_get_qdrant_client(),
                collection=COLLECTION_NAME,
                text=qtext,
                cat_keys=None,
                category_level_1=None,
                limit=DEFAULT_LIMIT,
                dedupe_mode="per_chunk",
            )
        except Exception as e:
            state.errors.append(f"qdrant_error: {e}")
            state.response = "ระบบค้นหาข้อมูลมีปัญหา กรุณาลองใหม่อีกครั้งค่ะ"
            return state

        if hits:
            any_bucket = _bucketize_any(hits, bucket_key="ทั่วไป")
            if any_bucket:
                _set_hits_by_category(state, any_bucket)
            state.response = "ยังไม่ทราบหมวดที่ต้องการ จึงแสดงเอกสารที่เกี่ยวข้องทั่วไปค่ะ"
            logger.info("[hybrid_search] no-category → no-filter → General bucket")
            return state

        # No hits at all → ask for clarification
        state.classification_result.clarification_needed = True
        state.classification_result.clarification_reason = (
            "ระบุหัวข้อย่อย เช่น อาหาร/กิจกรรม/ยา และประเภทหัตถการ"
        )
        state.response = (
            "ยังไม่พบข้อมูลที่ตรงประเด็นเลยค่ะ 🙏\n"
            "รบกวนเลือกหมวดที่เกี่ยวข้องเพื่อช่วยให้ค้นหาได้แม่นยำขึ้น:\n"
            "- หัตถการ (เช่น การใช้ยาชา)\n"
            "- อาการ/ภาวะแทรกซ้อน (เช่น ปวด เลือดออก แผลหายช้า)\n"
            "- การปฏิบัติตัวหลังทำหัตถการ (เช่น อาหาร การใช้หลอด การออกกำลังกาย สุรา สุขอนามัยช่องปาก)\n"
        )
        logger.info("[hybrid_search] no-category → no hits → clarify")
        return state

    # B) มีหมวดจาก classifier → filtered search (exact cat_keys → category_level_1 → no filter)
    cat_keys = [f"{a.level_1}|{a.level_2}" for a in cats]
    l1_list = sorted({a.level_1 for a in cats})

    try:
        hits = hybrid_search_qdrant(
            client=_get_qdrant_client(),
            collection=COLLECTION_NAME,
            text=qtext,  # latest-only
            cat_keys=cat_keys,
            category_level_1=l1_list,
            limit=DEFAULT_LIMIT,
            dedupe_mode="per_chunk",
        )
    except Exception as e:
        state.errors.append(f"qdrant_error: {e}")
        state.response = "ระบบค้นหาข้อมูลมีปัญหา กรุณาลองใหม่อีกครั้งค่ะ"
        return state

    if not hits:
        state.classification_result.clarification_needed = True
        state.classification_result.clarification_reason = "ระบุหัวข้อย่อย/ช่วงเวลา (เช่น วันแรก/สัปดาห์แรก)"
        state.response = "ยังไม่พบข้อมูลตรงประเด็น รบกวนระบุหัวข้อย่อยหรือช่วงเวลาหลังหัตถการค่ะ"
        logger.info("[hybrid_search] with-category → no hits → clarify")
        return state

    # Do retrieved chunks match the query’s categories? (cat_keys ∩ wanted ≠ ∅)
    wanted = set(cat_keys)
    buckets: Dict[str, List[RetrievalHit]] = {k: [] for k in wanted}

    for h in hits:
        p = h.get("payload") or {}
        matched = set(_as_list(p.get("cat_keys"))) & wanted
        if not matched:
            continue

        cid = p.get("chunk_id") or (str(h.get("id")) if h.get("id") is not None else "")
        if not cid:
            continue

        snip = p.get("text", "")
        for k in matched:
            buckets[k].append(
                RetrievalHit(
                    chunk_id=cid,
                    score=float(h.get("score", 0.0) or 0.0),
                    snippets=[snip] if snip else [],
                    metadata={
                        "title": p.get("title", ""),
                        **({"cat_keys": p.get("cat_keys")} if p.get("cat_keys") else {}),
                        **({"category_level_1": p.get("category_level_1")} if p.get("category_level_1") else {}),
                        **({"category_level_2": p.get("category_level_2")} if p.get("category_level_2") else {}),
                    },
                )
            )

    non_empty = {k: v for k, v in buckets.items() if v}

    if non_empty:
        _set_hits_by_category(state, non_empty)
        state.response = "พบเอกสารในหมวด: " + ", ".join(non_empty)
        logger.info("[hybrid_search] with-category → matched buckets = %d", len(non_empty))
        return state

    # มี hits แต่ไม่แมตช์หมวดที่ต้องการ → General
    any_bucket = _bucketize_any(hits, bucket_key="ทั่วไป")
    if any_bucket:
        _set_hits_by_category(state, any_bucket)
        state.response = "ไม่พบผลตรงหมวดที่คาดการณ์ จึงแสดงเอกสารที่เกี่ยวข้องทั่วไปค่ะ"
        logger.info("[hybrid_search] with-category → no matched bucket → General")
        return state

    # Fallback clarify
    state.classification_result.clarification_needed = True
    state.classification_result.clarification_reason = "ระบุหัวข้อย่อย/ช่วงเวลา (เช่น วันแรก/สัปดาห์แรก)"
    state.response = "ยังไม่พบข้อมูลตรงประเด็น รบกวนระบุหัวข้อย่อยหรือช่วงเวลาหลังหัตถการค่ะ"
    logger.info("[hybrid_search] with-category → fallback clarify")
    return state
