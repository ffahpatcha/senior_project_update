from qdrant_client import QdrantClient, models
import pandas as pd
import ast, json, re, os, time, sys, traceback
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import tqdm

# --------------- Load .env (robust) ---------------
ENV_PATH = find_dotenv(usecwd=True) or str(Path(__file__).resolve().parent / ".env")
loaded = load_dotenv(ENV_PATH, override=False)
print(f"🔎 .env loaded: {loaded} at {ENV_PATH}", flush=True)

def _getenv(key: str, default: str = "") -> str:
    return (os.getenv(key, default) or "").strip()

QDRANT_URL      = _getenv("QDRANT_URL")
QDRANT_API_KEY  = _getenv("QDRANT_API_KEY")
COLLECTION_NAME = _getenv("COLLECTION_NAME", "dental_chunks")
CSV_PATH        = r"output_with_keys.csv"

DENSE_VECTOR_NAME  = "dense"
SPARSE_VECTOR_NAME = "sparse"
DENSE_MODEL_NAME   = "intfloat/multilingual-e5-large"
SPARSE_MODEL_NAME  = "prithivida/Splade_PP_en_v1"

# --------------- Helpers ---------------
def parse_listish(x) -> list[str]:
    s = str(x or "").strip()
    if not s:
        return []
    try:
        v = json.loads(s)
    except Exception:
        try:
            v = ast.literal_eval(s)
        except Exception:
            v = [t.strip() for t in re.split(r"[;,]", s) if t.strip()]
    if isinstance(v, str):
        return [v.strip()] if v.strip() else []
    if isinstance(v, (list, tuple)):
        return [str(t).strip() for t in v if str(t).strip()]
    return []

def build_cat_fields(categories):
    """จากโครงสร้าง categories (list[dict]{level_1, level_2})
       -> คืน (cat_keys, category_level_1, category_level_2)
    """
    cat_keys, l1_set, l2_set = set(), set(), set()
    if isinstance(categories, dict):
        categories = [categories]
    if not isinstance(categories, (list, tuple)):
        return [], [], []
    for it in categories:
        if not isinstance(it, dict):
            continue
        l1 = str(it.get("level_1", "")).strip()
        l2 = str(it.get("level_2", "")).strip()
        if l1:
            l1_set.add(l1)
        if l2:
            l2_set.add(l2)
        if l1 and l2:
            cat_keys.add(f"{l1}|{l2}")
    return sorted(cat_keys), sorted(l1_set), sorted(l2_set)

def make_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60.0)

def check_qdrant(client: QdrantClient, retries: int = 3, delay: float = 1.5) -> bool:
    for i in range(1, retries+1):
        try:
            client.get_collections()
            print(f"✅ Qdrant reachable at {QDRANT_URL}", flush=True)
            return True
        except Exception as e:
            print(f"❌ Cannot reach Qdrant (try {i}/{retries}): {e}", flush=True)
            time.sleep(delay)
    return False

def _normalize_categories_raw(val) -> str:
    """บันทึก categories_raw เป็นสตริง (JSON) เพื่อ debug/ตรวจสอบย้อนหลัง"""
    if isinstance(val, (dict, list, tuple)):
        try:
            return json.dumps(val, ensure_ascii=False)
        except Exception:
            return str(val)
    return str(val or "")

def prepare_docs_and_payloads(df: pd.DataFrame):
    """เตรียม documents และ payloads ให้สอดคล้องกับฝั่ง hybrid (ใช้ category_level_1/2 + cat_keys)
       - ไม่เก็บ level_1_th ใน payload/ดัชนีอีกต่อไป
       - ยังรองรับการอ่านค่าจากคอลัมน์เก่า (level_1_th/level_2) เป็น fallback เท่านั้น
    """
    documents, payloads = [], []

    for i, (_, row) in enumerate(df.iterrows()):
        chunk = (row.get("chunk") or "").strip()
        if not chunk:
            continue

        # --- รับค่าจาก CSV (ชื่อใหม่เป็นหลัก) ---
        csv_cat_keys = parse_listish(row.get("cat_keys", ""))
        l1_new = parse_listish(row.get("category_level_1", ""))
        l2_new = parse_listish(row.get("category_level_2", ""))

        # --- fallback: ชื่อเก่า (อ่านได้ แต่จะไม่เก็บลง payload ในชื่อเก่า) ---
        l1_old = parse_listish(row.get("level_1_th", ""))  # read-only fallback
        l2_old = parse_listish(row.get("level_2", ""))     # read-only fallback

        l1_list = l1_new or l1_old
        l2_list = l2_new or l2_old

        use_csv_keys = bool(csv_cat_keys or l1_list or l2_list)

        if use_csv_keys:
            cat_keys = csv_cat_keys[:]  # copy
            if not cat_keys and l1_list and l2_list:
                cat_keys = [f"{l1}|{l2}" for l1 in l1_list for l2 in l2_list]

            category_level_1 = l1_list
            category_level_2 = l2_list
            categories_raw_for_payload = row.get("categories", "") or ""
        else:
            # พยายามอ่านคอลัมน์ categories (JSON/list)
            categories_raw = (row.get("categories") or "").strip()
            categories = None
            if categories_raw and categories_raw not in ("[]", "nan", "NaN", "None"):
                try:
                    try:
                        categories = json.loads(categories_raw)
                    except Exception:
                        categories = ast.literal_eval(categories_raw)
                except Exception as e:
                    print(f"⚠️ Failed to parse categories for chunk_id={row.get('chunk_id')}: {e}", flush=True)
            if not categories:
                continue

            cat_keys, category_level_1, category_level_2 = build_cat_fields(categories)
            categories_raw_for_payload = categories

        # --- ตรวจ chunk_id / doc_id ---
        doc_id   = str(row.get("doc_id", "")).strip()
        chunk_id = str(row.get("chunk_id", "")).strip()
        if not chunk_id:
            chunk_id = f"{doc_id or 'doc'}__chunk_{i:06d}"

        title   = str(row.get("title", "")).strip()
        source  = str(row.get("source", "")).strip()
        page    = str(row.get("page", "")).strip()
        section = str(row.get("section", "")).strip()
        url     = str(row.get("url", "")).strip()

        # --- เอกสารสำหรับสร้างเวกเตอร์ ---
        documents.append({
            DENSE_VECTOR_NAME:  models.Document(text=chunk, model=DENSE_MODEL_NAME),
            SPARSE_VECTOR_NAME: models.Document(text=chunk, model=SPARSE_MODEL_NAME),
        })

        # --- payload ให้สอดคล้องกับ hybrid (ไม่มี level_1_th แล้ว) ---
        payloads.append({
            "doc_id":            doc_id,
            "chunk_id":          chunk_id,
            "title":             title,
            "source":            source,
            "url":               url,
            "page":              page,
            "section":           section,
            "text":              chunk,
            "cat_keys":          cat_keys,                 # ["L1|L2", ...]
            "category_level_1":  category_level_1,         # ใหม่ (หลัก)
            "category_level_2":  category_level_2,         # ใหม่
            "categories_raw":    _normalize_categories_raw(categories_raw_for_payload),
        })

    return documents, payloads

def ensure_payload_indexes(client: QdrantClient, index_specs):
    for field, schema in index_specs:
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=schema
            )
            print(f"🔎 Created/exists index for '{field}' ({schema})", flush=True)
        except Exception as e:
            print(f"ℹ️ Skip '{field}': {e}", flush=True)

def wait_until_indexes_ready(client: QdrantClient, fields, timeout_sec: float = 20.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            info = client.get_collection(COLLECTION_NAME)
            schema = info.payload_schema or {}
            if all(k in schema for k in fields):
                print(f"✅ Indexes ready: {', '.join(fields)}", flush=True)
                return True
        except Exception as e:
            print(f"… waiting indexes: {e}", flush=True)
        time.sleep(0.5)
    print("⚠️ Indexes creation requested but not all visible yet.", flush=True)
    return False

# --------------- Main ---------------
def main():
    print(f"🔗 QDRANT_URL={QDRANT_URL!r} | API key set: {bool(QDRANT_API_KEY)} | COLLECTION_NAME={COLLECTION_NAME!r}", flush=True)

    missing = [k for k,v in {
        "QDRANT_URL": QDRANT_URL,
        "QDRANT_API_KEY": QDRANT_API_KEY,
    }.items() if not v]
    if missing:
        print(f"🛑 Missing env: {', '.join(missing)}  → ตรวจสอบไฟล์ .env แล้วรันใหม่", flush=True)
        return

    client = make_client()
    if not check_qdrant(client):
        print("🛑 Stop: Qdrant not reachable. เช็ก URL (https://…:6333), firewall/proxy, และ API key", flush=True)
        return

    print("📥 Loading CSV…", flush=True)
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if "doc_id" in df.columns:   df["doc_id"] = df["doc_id"].astype(str).str.strip()
    if "chunk_id" in df.columns: df["chunk_id"] = df["chunk_id"].astype(str).str.strip()

    documents, payloads = prepare_docs_and_payloads(df)
    print(f"✅ Prepared {len(documents)} docs", flush=True)
    if not documents:
        print("🛑 No documents to upload. Check CSV and parsing rules.", flush=True)
        return

    print("⏫ Uploading to Qdrant…", flush=True)
    client.upload_collection(
        collection_name=COLLECTION_NAME,
        vectors=tqdm.tqdm(documents),
        payload=payloads,
        parallel=1,
        batch_size=256,
    )
    print("🚀 Upload complete!", flush=True)

    print("🧭 Creating payload indexes…", flush=True)
    INDEX_SPECS = [
        ("doc_id",            models.PayloadSchemaType.KEYWORD),
        ("chunk_id",          models.PayloadSchemaType.KEYWORD),
        ("title",             models.PayloadSchemaType.KEYWORD),
        ("source",            models.PayloadSchemaType.KEYWORD),
        ("url",               models.PayloadSchemaType.KEYWORD),
        ("cat_keys",          models.PayloadSchemaType.KEYWORD),
        ("category_level_1",  models.PayloadSchemaType.KEYWORD),
        ("category_level_2",  models.PayloadSchemaType.KEYWORD),
        ("categories_raw",    models.PayloadSchemaType.KEYWORD),
    ]
    ensure_payload_indexes(client, INDEX_SPECS)
    wait_until_indexes_ready(client, [k for k, _ in INDEX_SPECS], timeout_sec=20.0)

    print("🎉 Done. You can now filter in Console by: cat_keys / category_level_1 / category_level_2 / doc_id", flush=True)

if __name__ == "__main__":
    try:
        print("▶ starting main()", flush=True)
        main()
        print("✅ finished", flush=True)
    except Exception as e:
        print(f"🛑 Fatal error: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
