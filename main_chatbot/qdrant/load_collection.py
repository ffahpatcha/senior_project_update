from qdrant_client import QdrantClient, models
import pandas as pd
import ast, json, re, os, time
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import tqdm

# --------------- Load .env (robust) ---------------
ENV_PATH = find_dotenv(usecwd=True) or str(Path(__file__).resolve().parent / ".env")
loaded = load_dotenv(ENV_PATH, override=False)
print(f"🔎 .env loaded: {loaded} at {ENV_PATH}")

def _getenv(key: str, default: str = "") -> str:
    return (os.getenv(key, default) or "").strip()

QDRANT_URL      = _getenv("QDRANT_URL")
QDRANT_API_KEY  = _getenv("QDRANT_API_KEY")
COLLECTION_NAME = _getenv("COLLECTION_NAME", "dental_chunks")
CSV_PATH        = r"output_with_keys.csv"

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
DENSE_MODEL_NAME = "intfloat/multilingual-e5-large"
SPARSE_MODEL_NAME = "prithivida/Splade_PP_en_v1"

# --------------- Helpers ---------------
def parse_listish(x) -> list[str]:
    s = str(x or "").strip()
    if not s: return []
    try:
        v = json.loads(s)
    except Exception:
        try:
            v = ast.literal_eval(s)
        except Exception:
            v = [t.strip() for t in re.split(r"[;,]", s) if t.strip()]
    if isinstance(v, str): return [v.strip()] if v.strip() else []
    if isinstance(v, (list, tuple)): return [str(t).strip() for t in v if str(t).strip()]
    return []

def build_cat_fields(categories):
    cat_keys, l1_set, l2_set = set(), set(), set()
    if isinstance(categories, dict):
        categories = [categories]
    if not isinstance(categories, (list, tuple)):
        return [], [], []
    for it in categories:
        if not isinstance(it, dict): continue
        l1 = str(it.get("level_1", "")).strip()
        l2 = str(it.get("level_2", "")).strip()
        if l1: l1_set.add(l1)
        if l2: l2_set.add(l2)
        if l1 and l2: cat_keys.add(f"{l1}|{l2}")
    return sorted(cat_keys), sorted(l1_set), sorted(l2_set)

def make_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60.0)

def check_qdrant(client: QdrantClient, retries: int = 3, delay: float = 1.5) -> bool:
    for i in range(1, retries+1):
        try:
            client.get_collections()
            print(f"✅ Qdrant reachable at {QDRANT_URL}")
            return True
        except Exception as e:
            print(f"❌ Cannot reach Qdrant (try {i}/{retries}): {e}")
            time.sleep(delay)
    return False

def prepare_docs_and_payloads(df: pd.DataFrame):
    documents, payloads = [], []
    for _, row in df.iterrows():
        chunk = (row.get("chunk") or "").strip()
        if not chunk:
            continue

        # Prefer CSV columns first
        cat_keys_csv   = parse_listish(row.get("cat_keys", ""))
        level_1_th_csv = parse_listish(row.get("level_1_th", ""))
        level_2_csv    = parse_listish(row.get("level_2", ""))  # only to derive cat_keys if needed

        use_csv_keys = bool(cat_keys_csv or level_1_th_csv or level_2_csv)

        if use_csv_keys:
            cat_keys   = cat_keys_csv
            level_1_th = level_1_th_csv
            if not cat_keys and level_1_th_csv and level_2_csv:
                cat_keys = [f"{l1}|{l2}" for l1 in level_1_th_csv for l2 in level_2_csv]
            categories_raw_for_payload = (row.get("categories", "") or "")
        else:
            categories_raw = (row.get("categories") or "").strip()
            categories = None
            if categories_raw and categories_raw not in ("[]", "nan", "NaN", "None"):
                try:
                    try: categories = json.loads(categories_raw)
                    except Exception: categories = ast.literal_eval(categories_raw)
                except Exception as e:
                    print(f"⚠️ Failed to parse categories for chunk_id={row.get('chunk_id')}: {e}")
            if not categories:
                continue
            cat_keys, level_1_th, _ = build_cat_fields(categories)
            categories_raw_for_payload = categories

        documents.append({
            DENSE_VECTOR_NAME: models.Document(text=chunk, model=DENSE_MODEL_NAME),
            SPARSE_VECTOR_NAME: models.Document(text=chunk, model=SPARSE_MODEL_NAME),
        })

        # Payload: ไม่มี title / level_2 / taxonomy_version
        payloads.append({
            "doc_id":     row.get("doc_id", ""),
            "chunk_id":   row.get("chunk_id", ""),
            "source":     row.get("source", ""),
            "page":       row.get("page", ""),
            "section":    row.get("section", ""),
            "text":       chunk,
            "cat_keys":   cat_keys,
            "level_1_th": level_1_th,
            "categories_raw": categories_raw_for_payload,
        })
    return documents, payloads

# --------------- Main ---------------
def main():
    print(f"🔗 QDRANT_URL={QDRANT_URL!r} | API key set: {bool(QDRANT_API_KEY)} | COLLECTION_NAME={COLLECTION_NAME!r}")

    # Hard-stop if env missing
    missing = [k for k,v in {
        "QDRANT_URL": QDRANT_URL,
        "QDRANT_API_KEY": QDRANT_API_KEY,
    }.items() if not v]
    if missing:
        print(f"🛑 Missing env: {', '.join(missing)}  → ตรวจสอบไฟล์ .env (ไม่มีช่องว่าง/พิมพ์ถูก) แล้วรันใหม่")
        return

    client = make_client()
    if not check_qdrant(client):
        print("🛑 Stop: Qdrant not reachable. เช็ก URL (ไม่มีช่องว่างข้างหน้า), firewall/proxy, และสิทธิ์คีย์")
        return

    # Index เฉพาะที่ใช้ค้น
    for field in ["cat_keys", "level_1_th"]:
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            print(f"🔎 Created/exists payload index for '{field}'")
        except Exception as e:
            print(f"ℹ️ Skipped index '{field}': {e}")

    # Load CSV & prepare
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    documents, payloads = prepare_docs_and_payloads(df)
    print(f"✅ Prepared {len(documents)} documents with dense+sparse vectors")

    # Upload — ใช้ parallel=1 บน Windows
    try:
        client.upload_collection(
            collection_name=COLLECTION_NAME,
            vectors=tqdm.tqdm(documents),
            payload=payloads,
            parallel=1,
            batch_size=256,
        )
        print("🚀 Upload complete!")
    except Exception as e:
        print(f"🛑 Upload failed: {e}")
        print("👉 ตรวจ URL/Key/สิทธิ์, ลด batch_size, หรืออัปโหลดแบบแบ่ง batch manual")

if __name__ == "__main__":
    main()
