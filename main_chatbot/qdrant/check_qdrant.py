from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from dotenv import load_dotenv
from pathlib import Path
import os
from typing import Optional, Dict
# โหลด .env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
COLLECTION_NAME="dental_collection"
# ค่า config จาก environment
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# ระบุชื่อของ vectors ใน collection
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
# เชื่อมต่อ Qdrant Client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)
dense_size = 1024
# ใช้ vector (ตัวอย่างนี้จะใช้ dense vector จากเอกสารที่อัปโหลด)
query_vector = [0.5] * dense_size  # สมมติว่า query vector มีค่าแบบสุ่ม, ต้องแทนที่ด้วยข้อมูลที่เหมาะสม
print("before search")
# ค้นหาเอกสารใน Qdrant
search_results = client.search(
    collection_name=COLLECTION_NAME,
    query_vector=query_vector,  # ใช้ vector สำหรับการค้นหา
    limit=5,  # จำกัดจำนวนผลลัพธ์
    with_payload=True,  # นำข้อมูล metadata มา
    with_vectors=True,  # เอา vector กลับมาด้วย
)
print("after search")
# แสดงผลลัพธ์ที่ได้
for result in search_results:
    print(f"Document ID: {result.id}")
    print(f"Categories: {result.payload['categories']}")
    print(f"Text: {result.payload['chunk_id']}")
    print(f"Distance: {result.score}")
    print()
