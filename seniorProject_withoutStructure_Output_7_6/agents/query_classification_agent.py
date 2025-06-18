from state_schema import AgentState, ClassificationResult, CategoryScore
from utils.llm_utils import get_together_llm
from config.settings import TOGETHER_MODEL
import json, re

# ---------- prompt ฝังตรงในตัวโค้ด ----------
prompt_template = """
บทบาทของคุณคือ "ผู้ช่วยจำแนกคำถามของผู้ป่วย" ที่อยู่ในช่วง **หลังทำหัตถการทางทันตกรรม (post oral surgery)** เช่น การถอนฟัน ผ่าฟันคุด ขูดหินปูน หรือรักษารากฟัน

---

### 🎯 เป้าหมายของคุณ:
เมื่อได้รับคำถามจากผู้ใช้ ให้ประเมินว่าเกี่ยวข้องกับประเด็นใดในการดูแลหลังหัตถการ และระบุความมั่นใจในแต่ละหมวดย่อยที่กำหนดไว้

---

### 🗂 หมวดย่อย (category_level_2):
1. อาหาร — สิ่งที่สามารถรับประทานได้หรือควรหลีกเลี่ยง, อาหารอ่อน, เวลาที่เริ่มกินได้หลังหัตถการ  
2. แผล — อาการของแผลผ่าตัด เช่น เลือดไหล แผลบวม หรือการสมานแผล  
3. อาการ/ภาวะแทรกซ้อน — เช่น ปวดมากผิดปกติ, มีไข้, หนอง, กลืนลำบาก  
4. การปฏิบัติตัวหลังทำหัตถการ — เช่น การแปรงฟัน บ้วนปาก การนอน การประคบเย็น  
5. การใช้ชีวิต — เช่น การกลับไปทำงาน ออกกำลังกาย สูบบุหรี่ ดื่มแอลกอฮอล์ เคี้ยวอาหาร  

---

### 🧠 เกณฑ์การให้คะแนน:
- หากคำถามมีคีย์เวิร์ดที่บ่งชี้ชัดเจนว่าอยู่ในบริบทของการดูแลหลังหัตถการ ให้ระบุหมวดที่เกี่ยวข้อง และให้ confidence ≥ 0.6  
- หากคำถามไม่มีคีย์เวิร์ดเกี่ยวข้องกับทันตกรรมหรือแสดงบริบทหลังหัตถการไม่ชัดเจน → confidence < 0.6 ทุกหมวด และ clarification_needed = true  
- หากความมั่นใจทุกหมวดต่ำกว่า 0.3 หรือไม่เกี่ยวข้องกับทันตกรรมเลย → out_of_domain = true

---

📌 ตอบกลับมาในรูปแบบ JSON เท่านั้น ดังนี้:

{
  "user_query": "{user_query}",
  "category_level_1": "patient",
  "category_level_2": [
    {"subcategory": "อาหาร", "confidence": 0.0},
    {"subcategory": "แผล", "confidence": 0.0},
    {"subcategory": "อาการ/ภาวะแทรกซ้อน", "confidence": 0.0},
    {"subcategory": "การปฏิบัติตัวหลังทำหัตถการ", "confidence": 0.0},
    {"subcategory": "การใช้ชีวิต", "confidence": 0.0}
  ],
  "clarification_needed": false,
  "out_of_domain": false
}

---

โปรดจำแนกคำถามต่อไปนี้โดยไม่ตอบคำถามอื่น:

{user_query}

ห้ามตอบคำถามอื่น หรือข้อมูลอื่นใดนอกเหนือจาก JSON ที่จำแนกคำถามนี้เท่านั้น
"""

# ---------- helper: ดึง JSON ก้อนแรก ----------
def extract_first_json(text: str) -> str:
    block = re.search(r"```json\s*({[\s\S]+?})\s*```", text)
    if block:
        return block.group(1)
    brace = re.search(r"{[\s\S]+?}", text)
    if brace:
        return brace.group(0)
    raise ValueError("ไม่พบ JSON ในข้อความ")

# ---------- agent หลัก ----------
def classify_query_agent(user_query: str) -> ClassificationResult:
    full_prompt = prompt_template.replace("{user_query}", user_query.strip())
    llm = get_together_llm(TOGETHER_MODEL)
    raw = llm.invoke(full_prompt)
    result_str = raw if isinstance(raw, str) else raw.get("text", "")


    try:
        json_str = extract_first_json(result_str)
        result_json = json.loads(json_str)

        return ClassificationResult(
            category_level_1=result_json["category_level_1"],
            category_level_2=[CategoryScore(**sub) for sub in result_json["category_level_2"]],
            clarification_needed=result_json["clarification_needed"],
            out_of_domain=result_json["out_of_domain"],
        )
    except Exception as e:
        raise ValueError(f"❌ JSON parse failed: {e}\n--- raw ---\n{result_str}")

# ---------- node สำหรับ LangGraph ----------
def classification_node(state: AgentState) -> AgentState:
    classification = classify_query_agent(state.user_query)
    return state.copy(update={"classification_result": classification})
