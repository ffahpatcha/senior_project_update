# 📁 agent.py
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from state_schema import (
    AgentState,
    ClassificationResult,
    CategoryScore,
    SubcategoryScore,
    ClarificationResult,
    CategoryResult
)
from utils.llm_utils import get_together_llm
from pydantic import BaseModel
from typing import List
from config.settings import TOGETHER_MODEL
import time
from utils.llm_utils import count_tokens

CATEGORY_SUBCATEGORY_MAPPING = {
    "หัตถการ": {"การใช้ยาชา"},
    "อาการ/ภาวะแทรกซ้อน": {"overall", "bleeding", "pain", "wound healing"},
    "การปฏิบัติตัวหลังทำหัตถการ": {"overall", "drinking straw", "alcohol", "workout", "food", "oral hygiene"}
}
CONFIDENCE_THRESHOLD = 0.4
def filter_invalid_categories(category_result):
    # กรอง category_level_1
    valid_level_1 = [
        cat for cat in category_result.category_level_1
        if cat.confidence >= CONFIDENCE_THRESHOLD and cat.category in CATEGORY_SUBCATEGORY_MAPPING
    ]

    # รวบรวมหมวดหลักที่ยังอยู่
    valid_main_categories = {cat.category for cat in valid_level_1}

    # กรอง category_level_2 ให้สัมพันธ์กับหมวดหลัก + confidence ผ่าน
    valid_level_2 = [
        sub for sub in category_result.category_level_2
        if sub.confidence >= CONFIDENCE_THRESHOLD and any(
            sub.subcategory in CATEGORY_SUBCATEGORY_MAPPING[main_cat]
            for main_cat in valid_main_categories
        )
    ]

    # อัปเดตผลลัพธ์
    category_result.category_level_1 = valid_level_1
    category_result.category_level_2 = valid_level_2
    return category_result


# ✅ Step 2: ตรวจสอบความชัดเจนของคำถาม
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
- [OUT] คือ คำตอบสุดท้ายในรูปแบบ JSON โดยมีค่า clarification_needed และ reason

<examples>
[IN] "ถอนฟันกรามกี่วันหายปวด"
[REASONING]
1. มีเจตนาถาม ชัดเจน ("กี่วัน")
2. มีบริบททางทันตกรรม (ปวดหลังถอนฟัน)
3. ระบุประเภทหัตถการชัดเจน (ถอนฟันกราม)
4. ข้อมูลเพียงพอสำหรับการให้คำแนะนำ
[OUT] {"clarification_needed": false, "reason": "คำถามชัดเจน มีบริบทและหัตถการครบถ้วน"}

[IN] "ยังเจ็บอยู่"
[REASONING]
1. ไม่มีเจตนาถาม เป็นประโยคบอกเล่า
2. ไม่มีบริบททางทันตกรรมที่ชัดเจน
3. ไม่รู้ว่าทำหัตถการอะไร
4. ข้อมูลไม่เพียงพอ
[OUT] {"clarification_needed": true, "reason": "ไม่มีคำถามหรือบริบทและไม่ระบุหัตถการ"}

[IN] "ยาชาหมดฤทธิ์กี่โมงคะ"  
[REASONING]  
1.มีเจตนาถาม  
2.มีบริบททางทันตกรรม ("ยาชา")  
3.ไม่ระบุว่าทำหัตถการอะไร  
4.ข้อมูลไม่เพียงพอ  
[OUT] {"clarification_needed": true, "reason": "ไม่ระบุประเภทของหัตถการ เช่น ถอนฟัน ผ่าฟันคุด ฯลฯ"}
                      
[IN] "ต้องทำยังไงดี"
[REASONING]
1. มีเจตนาถาม
2. ไม่มีบริบททางทันตกรรม (ไม่รู้ว่ามีอาการอะไร)
3. ไม่รู้ว่าทำหัตถการอะไร
4. ข้อมูลไม่เพียงพอ
[OUT] {"clarification_needed": true, "reason": "คำถามสั้น ไม่มีบริบทหรือหัตถการ"}

[IN] "ถอนฟันแล้วกินอะไรได้บ้าง"
[REASONING]
1. มีเจตนาถาม (ต้องการรู้ว่ากินอะไรได้)
2. มีบริบททางทันตกรรม (หลังถอนฟัน)
3. ระบุประเภทหัตถการชัดเจน (ถอนฟัน)
4. ข้อมูลเพียงพอสำหรับให้คำแนะนำ
[OUT] {"clarification_needed": false, "reason": "เจตนาชัดเจน มีบริบทและหัตถการครบ"}
</examples>

<format>
ตอบกลับเป็น JSON:
{
  "clarification_needed": true | false,
  "reason": "สั้น ๆ เพื่ออธิบายเหตุผล"
}
</format>

"""),
        HumanMessagePromptTemplate.from_template(
            "คำถาม: {user_query}\nโปรดตอบกลับเป็น JSON ตาม <format>"
        )
    ])
    chain = prompt | llm
    return chain.invoke({"user_query": user_query})

# ✅ Step 3: จัดหมวดหมู่คำถาม
def classify_categories(user_query: str) -> CategoryResult:
    llm = get_together_llm(
        model=TOGETHER_MODEL,
        structured_output_schema=CategoryResult,
        temperature=0.1
    )
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
คุณคือระบบช่วยจำแนกคำถามจากผู้ป่วยหลังทำหัตถการทางทันตกรรม  
คุณต้องจำแนกคำถามออกเป็นหมวดหมู่หลัก (`category_level_1`) และหมวดย่อย (`category_level_2`) พร้อมความมั่นใจ (confidence)

<หมวดหมู่หลักที่อนุญาตให้ตอบ (category_level_1)>
- หัตถการ
- อาการ/ภาวะแทรกซ้อน
- การปฏิบัติตัวหลังทำหัตถการ

<หมวดย่อย (category_level_2) ที่สัมพันธ์กับหมวดหลัก>
- หัตถการ:
    - การใช้ยาชา
- อาการ/ภาวะแทรกซ้อน:
    - overall
    - bleeding
    - pain
    - wound healing
- การปฏิบัติตัวหลังทำหัตถการ:
    - overall
    - drinking straw
    - alcohol
    - workout
    - food
    - oral hygiene

<category_level_2 definitions>
- การใช้ยาชา: คำถามเกี่ยวกับชนิด วิธีใช้ หรือระยะเวลาของฤทธิ์ยาชา
- overall (อาการ/ภาวะแทรกซ้อน): คำถามเกี่ยวกับอาการผิดปกติรวม ๆ เช่น ควรพบแพทย์เมื่อใด
- bleeding: คำถามเกี่ยวกับเลือด เช่น เลือดไหล เลือดไม่หยุด
- pain: คำถามเกี่ยวกับความปวด เช่น ปวดไม่หาย กินยาแล้วไม่ดีขึ้น
- wound healing: คำถามเกี่ยวกับแผลหาย ฟื้นตัว เช่น แผลหายเมื่อไหร่ หายช้าหรือไม่
- overall (การปฏิบัติตัวหลังทำหัตถการ): คำถามเกี่ยวกับพฤติกรรมโดยรวมหลังหัตถการ
- drinking straw: คำถามเกี่ยวกับการใช้หลอด
- alcohol: การดื่มแอลกอฮอล์
- workout: การออกกำลังกาย
- food: คำถามเกี่ยวกับอาหารที่กินได้/ไม่ได้ เช่น ของแข็ง เผ็ด ร้อน
- oral hygiene: คำถามเกี่ยวกับการบ้วนปาก แปรงฟัน หรือใช้น้ำยาบ้วนปาก
</category_level_2 definitions>

<ข้อกำหนด>
- หมวดย่อยต้องสัมพันธ์กับหมวดหลักเท่านั้น
- คำถาม 1 ข้อ อาจมีได้มากกว่า 1 หมวดหมู่และหมวดย่อย
- ห้ามสร้างหมวดหมู่ใหม่หรือใช้คำอื่นนอกจากที่กำหนด
- confidence ต้องอยู่ระหว่าง 0.0 - 1.0

<format>
{
  "category_level_1": [
    {"category": "ชื่อหมวดหลัก", "confidence": 0.0 - 1.0},
    ...
  ],
  "category_level_2": [
    {"subcategory": "ชื่อหมวดย่อย", "confidence": 0.0 - 1.0},
    ...
  ]
}
</format>

<ตัวอย่าง>
[IN] ถอนฟันมาแล้วปวดมาก กินอะไรได้บ้าง?
[OUT]
{
  "category_level_1": [
    {"category": "อาการ/ภาวะแทรกซ้อน", "confidence": 0.93},
    {"category": "การปฏิบัติตัวหลังทำหัตถการ", "confidence": 0.91}
  ],
  "category_level_2": [
    {"subcategory": "pain", "confidence": 0.91},
    {"subcategory": "food", "confidence": 0.88}
  ]
}
[IN] แผลถอนฟันจะหายสนิทในเวลากี่วัน?
[OUT]
{
  "category_level_1": [{"category": "อาการ/ภาวะแทรกซ้อน", "confidence": 0.91}],
  "category_level_2": [{"subcategory": "wound healing", "confidence": 0.90}]
}
[IN] แผลถอนฟันหายนานแค่ไหน
[OUT]
{
  "category_level_1": [{"category": "อาการ/ภาวะแทรกซ้อน", "confidence": 0.90}],
  "category_level_2": [{"subcategory": "wound healing", "confidence": 0.89}]
}
"""),
        HumanMessagePromptTemplate.from_template(
            "คำถาม: {user_query}\nโปรดตอบกลับเป็น JSON ตาม schema ที่กำหนด"
        )
    ])
    chain = prompt | llm
    raw_result = chain.invoke({"user_query": user_query})
    filtered_result = filter_invalid_categories(raw_result)
    return filtered_result

# Pipeline หลังลบ Out-of-Domain ออก
def run_classification_pipeline(state: AgentState) -> AgentState:
    latency_info = {}

    merged_query = (
        "\n".join(state.previous_turns + [state.user_query])
        if state.previous_turns else state.user_query
    )

    print("🔍 Step 1: Clarity Check")
    start = time.perf_counter()
    clarity_result = check_clarity(state.user_query)
    print("✅ Clarity Result:", clarity_result)
    latency_info["clarification"] = round(time.perf_counter() - start, 3)
    latency_info["tokens_clarification"] = count_tokens(state.user_query, model=TOGETHER_MODEL)
    state.classification_result.clarification_needed = clarity_result.clarification_needed
    state.classification_result.clarification_reason = clarity_result.reason
    if state.should_terminate():
        state.latency = latency_info
        return state

    print("📊 Step 2: Category Classification")
    start = time.perf_counter()
    category_result = classify_categories(state.user_query)
    latency_info["classification"] = round(time.perf_counter() - start, 3)
    latency_info["tokens_classification"] = count_tokens(state.user_query, model=TOGETHER_MODEL)
    state.classification_result.category_level_1 = category_result.category_level_1
    state.classification_result.category_level_2 = category_result.category_level_2
    state.latency = latency_info
    return state
