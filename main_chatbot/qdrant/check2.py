from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os

# โหลดค่าจากไฟล์ .env
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
# เชื่อมต่อกับ Qdrant
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# ตรวจสอบสถานะการเชื่อมต่อ
try:
    # ลองดึงข้อมูลจากคอลเล็กชันหนึ่งใน Qdrant
    collection_info = client.get_collection(collection_name="dental_chunks")
    print("Successfully connected to Qdrant!")
    print(collection_info) 
except Exception as e:
    print("Failed to connect to Qdrant:", str(e))


# ตรวจสอบว่าได้ค่าจาก .env หรือไม่
print("QDRANT_URL:", QDRANT_URL)
print("QDRANT_API_KEY:", QDRANT_API_KEY)
