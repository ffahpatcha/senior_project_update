# 📁 utils/query_rewrite.py

def auto_rewrite_query(previous_user_query: str, clarification_prompt: str, user_reply: str) -> str:
    """
    รวม query ก่อนหน้า + การถามกลับ + คำตอบล่าสุดของผู้ใช้ → เป็น query ที่สมบูรณ์
    """
    if any(word in clarification_prompt for word in ["หัตถการ", "ประเภท", "ชนิด", "แบบไหน"]) and len(user_reply.strip().split()) <= 6:
        return f"{user_reply.strip()} อยากทราบว่า {previous_user_query.strip()}"
    
    return f"{previous_user_query.strip()} {user_reply.strip()}"  # fallback
