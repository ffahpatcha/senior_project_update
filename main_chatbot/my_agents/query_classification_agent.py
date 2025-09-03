# 📁 query classification agent.py
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from state_schema import (
    ClarificationResult,
    CategoryAssignment,
)
from taxonomy import norm, valid_pair, canonical_l1, canonical_l2
from llm_utils import get_together_llm,count_tokens
from settings import TOGETHER_MODEL
from pydantic import BaseModel, Field
from typing import List

# ---- LLM output schemas (เฉพาะเอเจนต์นี้) ----
class CategoryAssignmentOut(BaseModel):
    level_1: str = Field(..., description="ไทย เช่น 'การปฏิบัติตัวหลังทำหัตถการ'")
    level_2: str = Field(..., description="EN เช่น 'oral hygiene'")
    score: float = Field(..., ge=0.0, le=1.0)

class ClassificationLLMResult(BaseModel):
    categories: List[CategoryAssignmentOut] = Field(default_factory=list)

# -------- Clarify --------ม
def check_clarity(user_query: str) -> ClarificationResult:
    llm = get_together_llm(
        model=TOGETHER_MODEL,
        structured_output_schema=ClarificationResult,
        temperature=0.1
    )
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
คุณคือระบบช่วยวิเคราะห์คำถามจากผู้ป่วยหลังหัตถการทางทันตกรรม โดยต้องวินิจฉัยว่า ข้อความต้องการการขยายความเพิ่มเติมหรือไม่ในบริบทของหารให้คำแนะนำหลังทำหัตถการสำหรับผู้ป่วย

ในส่วนถัดไป:
- `<task>` คือ คำอธิบายขั้นตอนการให้เหตุผลแบบลำดับขั้น (Chain of Thought) ที่ระบบต้องทำตาม เพื่อประเมินว่าข้อมูลที่ได้รับเพียงพอหรือไม่
- `<criteria>` คือ เงื่อนไขการตัดสินผลลัพธ์ ว่าควรตอบว่า `clarification_needed: true` หรือ `false` ขึ้นอยู่กับการประเมินจาก task แต่ละข้อ
<task>
ประเมินข้อความของผู้ใช้โดยใช้เหตุผลแบบ Chain of Thought (CoT) ตามลำดับตรรกะต่อไปนี้ (short-circuit evaluation):

ดำเนินการตรวจสอบทีละข้อเรียงลำดับ หากเจอข้อใด "ไม่เป็นจริง (false)" ให้หยุดการประเมินทันที  
และตอบว่า:
  {"clarification_needed": true, "clarification_reason": "<เหตุผลที่ไม่ผ่าน>"}
[กติกาการประเมิน (ลำดับหยุดเมื่อไม่ผ่าน)]
1. ข้อความมีเจตนาถามหรือไม่  
   - ข้อความต้องมีลักษณะเป็นคำถาม เช่น ใช้คำว่า อะไร, อย่างไร, ได้ไหม, เมื่อไร, ควรไหม, ทำยังไง  
   - ถ้าเป็นแค่ข้อความบอกเล่า เช่น “ยังเจ็บอยู่”, “เลือดออกเยอะ” → ถือว่าไม่มีเจตนาถาม  
   → หากไม่ใช่คำถาม → หยุดการประเมิน  
   → clarification_reason: "ไม่มีเจตนาถาม"

2. มีการระบุประเภทของหัตถการหรือไม่  
   - ต้องกล่าวถึง **ชื่อหัตถการ** อย่างชัดเจน เช่น ถอนฟัน, ผ่าฟันคุด, ขูดหินปูน, อุดฟัน, รักษารากฟัน, ผ่าตัดเหงือก, ตัดแต่งเหงือก ฯลฯ  
   - ถ้ากล่าวถึงแค่การกระทำทั่วไป เช่น "ทำฟัน", "หลังหาหมอ", "ตอนกลับบ้าน", "ตอนฟันซี่นั้นหลุด" โดยไม่บอกว่า **ทำหัตถการใด** → ให้ถือว่า **ไม่ระบุหัตถการ**  
   - คำถามที่เกี่ยวกับพฤติกรรมหลังทำ เช่น "แปรงฟันได้ไหม", "ใช้หลอดดูดได้ไหม", "บ้วนปากได้ไหม" → ต้องมีการอ้างอิงว่าหัตถการอะไรจึงจะเพียงพอ  
   → หากไม่มีการระบุชัดเจน → หยุด  
   → clarification_reason: "ไม่ระบุประเภทของหัตถการ เช่น ถอนฟัน ผ่าฟันคุด ฯลฯ"

3. มีบริบททางทันตกรรมหรือไม่  
   - ต้องมีคำที่สื่อถึงปัญหาหรือการดูแลช่องปาก เช่น ฟัน เหงือก เจ็บ ปวด แผล เลือด ยาชา บวม เย็บแผล รากฟัน หรืออาการหลังทำฟัน  
   - หากไม่มีคำเหล่านี้เลย หรือไม่สามารถสรุปได้ว่าเกี่ยวข้องกับทันตกรรมโดยตรง → ถือว่าไม่มีบริบท  
   - คำที่คลุมเครือ เช่น “ปวด”, “ชา”, “แสบ”, “หายหรือยัง” → ต้องดูว่าผูกโยงกับบริบททางช่องปากหรือไม่  
   → หากไม่มีบริบททางทันตกรรม → หยุด  
   → clarification_reason: "ไม่มีบริบททางทันตกรรม"

4. ข้อมูลเพียงพอสำหรับการให้คำแนะนำทันทีหรือไม่  
   - หมายถึง ผ่านครบ 3 ข้อข้างต้น (คำถาม + หัตถการ + บริบท) และสามารถตอบกลับโดยไม่ต้องถามเพิ่ม  
   - หากคำถามกว้างเกินไป เช่น "ควรทำยังไงดี", "กินยาอะไรได้บ้าง", หรือขาดคำสำคัญ เช่น ไม่บอกอาการ/บริบท/ช่วงเวลา → ถือว่าไม่เพียงพอ  
   → หากยังไม่ครบ → หยุด  
   → clarification_reason: "ข้อมูลยังไม่เพียงพอสำหรับให้คำแนะนำ"

หากผ่านทั้ง 4 ข้อ ให้ตอบว่า:
  {"clarification_needed": false}
เมื่อ "clarification_needed": true ให้เขียน clarification_reason เป็น "ข้อความมิตรภาพ + เช็กลิสต์ + ตัวอย่าง" ตามแบบนี้ (ห้ามตอบสั้น ๆ ประโยคเดียว):
- ขึ้นต้นสุภาพ: "ขอข้อมูลเพิ่มนิดนึงนะคะ/ครับ เพื่อแนะนำได้ตรงขึ้นค่ะ/ครับ"
- ระบุสิ่งที่ขาดชัดเจน (เหตุผลจากข้อที่ไม่ผ่าน)
- ตามด้วยหัวข้อบูลเล็ต 2–4 ข้อ ว่าต้องการอะไร เช่น:
  • ประเภทหัตถการ (เช่น ถอนฟัน/ผ่าฟันคุด/อุดฟัน/ขูดหินปูน)
  • เวลาหลังทำ (เช่น กี่ชั่วโมง/กี่วันแล้ว)
  • อาการหลักและความรุนแรง (เช่น ปวดระดับ 0–10, เลือดซึม/บวม/มีไข้)
  • ยาที่ใช้อยู่/แพ้ยา (ถ้ามี)
- ปิดท้ายด้วย "ตัวอย่างที่พิมพ์ได้เลย" 2–3 ข้อ (ให้เป็นประโยคที่พร้อมส่ง เช่น
  • "ผ่าฟันคุดมา 24 ชม. เลือดซึม ควรทำอย่างไรดี?"
  • "ถอนฟันมา 2 วัน ปวดระดับ 6/10 กินยาอะไรได้บ้างตามใบแพทย์สั่ง?"
)

ข้อควรทำสไตล์:
- น้ำเสียงอบอุ่น ไม่ตำหนิ ใช้คำว่า “ค่ะ/ครับ” แบบรวมได้
- กระชับ อ่านง่าย ไม่ยาวเกิน ~4 บูลเล็ต
- หลีกเลี่ยงการวินิจฉัย/สั่งยาในส่วน reason นี้
- ถ้าเข้าข่ายฉุกเฉิน (เช่น เลือดออกมากไม่หยุด/ไข้สูง/กลืนลำบาก/หายใจลำบาก) ให้ใส่ประโยคเตือนท้ายสั้น ๆ ว่าให้ไปพบแพทย์ทันที
</task>

<criteria>
- ถ้าพบข้อใด “ไม่ผ่าน” → ตอบ:
  {
    "clarification_needed": true,
    "clarification_reason": "<เหตุผลที่ไม่ผ่านจากข้อที่ตรวจสอบ>"
  }

- ถ้าผ่านครบทั้ง 4 ข้อ → ตอบ:
  {
    "clarification_needed": false
  }
</criteria>

ด้านล่างคือตัวอย่างการให้เหตุผลและการตัดสินค่า clarification_needed:
- [IN] คือ ข้อความที่ผู้ใช้ส่งเข้ามา
- [REASONING] คือ การให้เหตุผลตามเกณฑ์ทั้ง 4 ข้อ (เจตนาถาม, บริบททางทันตกรรม, ประเภทหัตถการ, ข้อมูลเพียงพอ)
- [OUT] คือ คำตอบสุดท้ายในรูปแบบ JSON โดยมีค่า clarification_needed และ clarification_reason

<examples>
[IN] "ถอนฟันกรามกี่วันหายปวด"
[REASONING]
1. มีเจตนาถาม ชัดเจน ("กี่วัน")
2. มีบริบททางทันตกรรม (ปวดหลังถอนฟัน)
3. ระบุประเภทหัตถการชัดเจน (ถอนฟันกราม)
4. ข้อมูลเพียงพอสำหรับการให้คำแนะนำ
[OUT] {"clarification_needed": false, "clarification_reason": "คำถามชัดเจน มีบริบทและหัตถการครบถ้วน"}

[IN] "ยังเจ็บอยู่"
[REASONING]
1. ไม่มีเจตนาถาม เป็นประโยคบอกเล่า
2. ไม่มีบริบททางทันตกรรมที่ชัดเจน
3. ไม่รู้ว่าทำหัตถการอะไร
4. ข้อมูลไม่เพียงพอ
[OUT] {"clarification_needed": true, "clarification_reason": "ไม่มีคำถามหรือบริบทและไม่ระบุหัตถการ"}

[IN] "ยาชาหมดฤทธิ์กี่โมงคะ"  
[REASONING]  
1.มีเจตนาถาม  
2.มีบริบททางทันตกรรม ("ยาชา")  
3.ไม่ระบุว่าทำหัตถการอะไร  
4.ข้อมูลไม่เพียงพอ  
[OUT] {"clarification_needed": true, "clarification_reason": "ไม่ระบุประเภทของหัตถการ เช่น ถอนฟัน ผ่าฟันคุด ฯลฯ"}
                      
[IN] "ต้องทำยังไงดี"
[REASONING]
1. มีเจตนาถาม
2. ไม่มีบริบททางทันตกรรม (ไม่รู้ว่ามีอาการอะไร)
3. ไม่รู้ว่าทำหัตถการอะไร
4. ข้อมูลไม่เพียงพอ
[OUT] {"clarification_needed": true, "clarification_reason": "คำถามสั้น ไม่มีบริบทหรือหัตถการ"}

[IN] "ถอนฟันแล้วกินอะไรได้บ้าง"
[REASONING]
1. มีเจตนาถาม (ต้องการรู้ว่ากินอะไรได้)
2. มีบริบททางทันตกรรม (หลังถอนฟัน)
3. ระบุประเภทหัตถการชัดเจน (ถอนฟัน)
4. ข้อมูลเพียงพอสำหรับให้คำแนะนำ
[OUT] {"clarification_needed": false, "clarification_reason": "เจตนาชัดเจน มีบริบทและหัตถการครบ"}
</examples>

<format>
ตอบกลับเป็น JSON เท่านั้น:
{
  "clarification_needed": true | false,
  "clarification_reason": "string (ใส่เมื่อเป็น true)"
}
</format>
"""),
        HumanMessagePromptTemplate.from_template(
            "คำถาม: {user_query}\nโปรดตอบกลับเป็น JSON ตาม <format>"
        )
    ])
    chain = prompt | llm
    raw_output = chain.invoke({"user_query": user_query})
    if raw_output is None:
      return ClarificationResult(clarification_needed=True,
                                clarification_reason="ระบบไม่สามารถประมวลผลคำถามได้ โปรดลองใหม่ค่ะ")
    if isinstance(raw_output, dict):
      if "clarification_reason" not in raw_output and "reason" in raw_output:
          raw_output["clarification_reason"] = raw_output.pop("reason")
      return ClarificationResult(**raw_output)
    return raw_output


def classify_categories(user_query: str) -> List[CategoryAssignment]:
    llm = get_together_llm(
        model=TOGETHER_MODEL,
        structured_output_schema=ClassificationLLMResult,
        temperature=0.1
    )

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""คุณคือระบบช่วยจำแนกคำถามจากผู้ป่วยหลังทำหัตถการทางทันตกรรม  
คุณต้องจำแนกคำถามออกเป็นหมวดหมู่หลัก (`category_level_1`) และหมวดย่อย (`category_level_2`) พร้อมความมั่นใจ (confidence)
                      
ข้อกำหนดสำคัญ
- คิดเหตุผลภายใน แต่ห้ามอธิบายเหตุผลออกมา
- ตอบกลับเป็น JSON ตาม <format> เท่านั้น
- ใช้ค่าจาก whitelist ด้านล่างเท่านั้น ห้ามสร้างคำใหม่/ห้ามสะกดเพี้ยน/ห้ามเปลี่ยนตัวพิมพ์เล็ก-ใหญ่
- 1 คำถาม อนุญาตหลายคู่ (โดยทั่วไปไม่เกิน 3 คู่) และ level_2 ต้องสัมพันธ์กับ level_1
                      
<หมวดหมู่หลักที่อนุญาตให้ตอบ (category_level_1)>
- "หัตถการ"
- "อาการภาวะแทรกซ้อน"  
- "การปฏิบัติตัวหลังทำหัตถการ"

<whitelist หมวดย่อย (category_level_2) ที่สัมพันธ์กับหมวดหลัก>
- หัตถการ:
    - "extraction"
    - "surgical removal of impacted teeth"
    - "dental implant surgery"
- อาการภาวะแทรกซ้อน:
    - "Physical Symptoms"
    - "Digestive and Body Reactions"
    - "Wound and Infection"
    - "Respiratory and Throat"
- การปฏิบัติตัวหลังทำหัตถการ:
    - "all rounded post op instruction"
    - "sleeping"
    - "drinking straw"
    - "smoking"
    - "alcohol"
    - "workout"
    - "food"
    - "oral hygiene"
    - "compression"
    - "medicine"
- ใช้ string ให้ “ตรงตามรายการ” เท่านั้น ห้ามมีสแลช/สะกดต่าง/เคสต่าง
<category_level_2 definitions>
- extraction: ถอนฟัน
- surgical removal of impacted teeth: ผ่าตัดนำฟันคุดออก
- dental implant surgery: ผ่าตัดฝังรากเทียม
- Physical Symptoms: อาการกายภาพ เช่น ปวด บวม ชา ตึง
- Digestive and Body Reactions: ปฏิกิริยาทางระบบ/ทางเดินอาหาร เช่น คลื่นไส้ เวียนหัว อ่อนเพลีย
- Wound and Infection: เรื่องแผล/การหายของแผล/สัญญาณติดเชื้อ
- Respiratory and Throat: ทางเดินหายใจและคอ เช่น ไอ เจ็บคอ เสมหะ หายใจลำบาก
- all rounded post op instruction: คำแนะนำภาพรวมหลังทำ
- sleeping: วิธี/ท่านอน/การหนุนหมอนหลังทำ
- drinking straw: การใช้หลอดดูด
- smoking: การสูบบุหรี่/บุหรี่ไฟฟ้า
- alcohol: การดื่มแอลกอฮอล์
- workout: การออกกำลังกาย/ยกของหนัก
- food: อาหารที่ควร/ไม่ควร
- oral hygiene: แปรงฟัน บ้วนปาก น้ำยาบ้วนปาก
- compression: กัดผ้าก๊อซ/การประคบกด
- medicine: การใช้ยาแก้ปวด/ยาปฏิชีวนะ/ยาอื่น ๆ

<ข้อกำหนด>
- หมวดย่อยต้องสัมพันธ์กับหมวดหลักเท่านั้น
- คำถาม 1 ข้อ อาจมีได้มากกว่า 1 หมวดหมู่และหมวดย่อย
- ห้ามสร้างหมวดหมู่ใหม่หรือใช้คำอื่นนอกจากที่กำหนด
- confidence ต้องอยู่ระหว่าง 0.0 - 1.0

<hints>
- ถ้าพูดถึง “ผ่าฟันคุด” ให้ใส่คู่หัตถการด้วย: level_1="หัตถการ", level_2="surgical removal of impacted teeth"
- ถ้าถามพฤติกรรมหลังทำ (แปรงฟัน บ้วนปาก หลอด บุหรี่ แอลกอฮอล์ ออกกำลัง นอน ประคบ ยา อาหาร) ให้เข้ากลุ่ม “การปฏิบัติตัวหลังทำหัตถการ” และเลือก level_2 ให้ตรง
- ถ้าพูดถึงอาการผิดปกติ (ปวด บวม เลือด ติดเชื้อ เจ็บคอ ไอ ฯลฯ) ให้เข้ากลุ่ม “อาการภาวะแทรกซ้อน” แล้วเลือก level_2 ที่ตรงที่สุด
<format>
{
  "categories": [
    {"level_1": "<ไทยตาม whitelist>", "level_2": "<ตาม whitelist>", "score": 0.0-1.0},
    ...
  ]
}
</format>
                      
<examples>
[IN] "ผ่าฟันคุดมาเมื่อวาน ปวดเยอะ ใช้หลอดดูดได้ไหม"
[OUT]
{
  "categories": [
    {"level_1": "หัตถการ", "level_2": "surgical removal of impacted teeth", "score": 0.88},
    {"level_1": "อาการภาวะแทรกซ้อน", "level_2": "Physical Symptoms", "score": 0.86},
    {"level_1": "การปฏิบัติตัวหลังทำหัตถการ", "level_2": "drinking straw", "score": 0.93}
  ]
}

[IN] "ถอนฟันแล้วเลือดซึมตลอด ควรทำยังไง"
[OUT]
{
  "categories": [
    {"level_1": "หัตถการ", "level_2": "extraction", "score": 0.86},
    {"level_1": "อาการภาวะแทรกซ้อน", "level_2": "Wound and Infection", "score": 0.90},
    {"level_1": "การปฏิบัติตัวหลังทำหัตถการ", "level_2": "compression", "score": 0.84}
  ]
}

[IN] "ทำรากเทียมมา แปรงฟัน บ้วนปาก และกินยาแก้อักเสบยังไงดี"
[OUT]
{
  "categories": [
    {"level_1": "หัตถการ", "level_2": "dental implant surgery", "score": 0.90},
    {"level_1": "การปฏิบัติตัวหลังทำหัตถการ", "level_2": "oral hygiene", "score": 0.88},
    {"level_1": "การปฏิบัติตัวหลังทำหัตถการ", "level_2": "medicine", "score": 0.85}
  ]
}
</examples>
"""),
        HumanMessagePromptTemplate.from_template(
            "คำถาม: {user_query}\nโปรดตอบกลับเป็น JSON ตาม <format> เท่านั้น"
        )
    ])

    chain = prompt | llm
    llm_out: ClassificationLLMResult = chain.invoke({"user_query": user_query})
    if not llm_out or not llm_out.categories:
        return []

    # map → CategoryAssignment (สคีมาหลักใน state) + ใส่ source="clf_v2"
    # พร้อม dedupe โดยเก็บคะแนนสูงสุดต่อคู่
    best = {}
    for it in llm_out.categories or []:
        l1_raw, l2_raw = it.level_1, it.level_2

        # normalize + canonicalize
        l1c = canonical_l1(norm(l1_raw))
        l2c = canonical_l2(norm(l2_raw))

        if not valid_pair(l1c, l2c):
            print("[clf][DROP invalid_pair]", repr(l1_raw), "→", l1c, "|", repr(l2_raw), "→", l2c)
            continue

        k = f"{l1c}|{l2c}"
        if (k not in best) or (it.score > best[k].score):
            best[k] = CategoryAssignment(
                level_1=l1c,
                level_2=l2c,
                score=it.score,
                source=TOGETHER_MODEL,
            )

    # คืนลิสต์พร้อมใช้งาน (state validator จะทำ threshold/จัดลำดับอีกชั้น)
    return sorted(best.values(), key=lambda x: x.score, reverse=True)
