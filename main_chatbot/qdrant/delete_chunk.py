# clear_qdrant_points.py
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv, find_dotenv
import os

# Load .env
load_dotenv(find_dotenv(usecwd=True))
QDRANT_URL = (os.getenv("QDRANT_URL") or "").strip()
QDRANT_API_KEY = (os.getenv("QDRANT_API_KEY") or "").strip()
COLLECTION_NAME = (os.getenv("COLLECTION_NAME") or "dental_chunks").strip()

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60.0)

# เช็คว่า collection มีอยู่
client.get_collection(collection_name=COLLECTION_NAME)
print(f"✅ Connected. Collection '{COLLECTION_NAME}' is available.")

# ไล่ลบเป็นแบตช์
deleted_total = 0
next_page = None
BATCH = 1000

while True:
    points, next_page = client.scroll(
        collection_name=COLLECTION_NAME,
        with_payload=False,
        with_vectors=False,
        limit=BATCH,
        offset=next_page,
    )
    ids = [p.id for p in points]
    if not ids:
        break

    # ใช้ .delete (ไม่ใช่ .delete_points)
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.PointIdsList(points=ids),
        wait=True,
    )
    deleted_total += len(ids)
    print(f"🧹 Deleted {deleted_total} points...", end="\r")

# ตรวจยอดคงเหลือ
remaining = client.count(collection_name=COLLECTION_NAME, exact=True).count
print(f"\n✅ Done. Remaining points: {remaining}")
