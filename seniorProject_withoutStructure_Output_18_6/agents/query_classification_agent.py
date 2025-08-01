# 📁 agent.py
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from state_schema import (
    AgentState,
    ClassificationResult,
    CategoryScore,
    SubcategoryScore,
    OutOfDomainResult,
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


from langchain_core.prompts import HumanMessagePromptTemplate

def check_out_of_domain(user_query: str) -> OutOfDomainResult:
    llm = get_together_llm(
        model=TOGETHER_MODEL,
        structured_output_schema=OutOfDomainResult,
        temperature=0.1
    )
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
หน้าที่ของคุณคือทำตามคำอธิบายใน `<task>`  
จากนั้นให้ใช้เกณฑ์จาก `<criteria>` รวมถึงข้อมูลจาก `<scope_schema>`, `<examples_in_scope>`, `<examples_out_of_scope>`, `<guideline>`, `<output_format>`, และ `<examples>` เพื่อช่วยตัดสินว่า  
"คำถามของผู้ใช้" อยู่ในขอบเขตของระบบหรือไม่

คำอธิบายของแต่ละ tag มีดังนี้:
- `<task>`: ระบุหน้าที่หลักของคุณว่าต้องกรองคำถามก่อนส่งต่อ หากคำถามไม่เกี่ยวกับ "ทันตกรรมหลังหัตถการ" ให้ตอบว่าข้อมูลอยู่นอกขอบเขต (`out_of_domain: true`)
- `<criteria>`: เป็นเกณฑ์สำคัญที่ระบุอย่างชัดเจนว่าระบบนี้รองรับเฉพาะคำถามเกี่ยวกับ **การดูแลหลังหัตถการทางทันตกรรม** เท่านั้น โดยมีตัวอย่างของสิ่งที่อยู่ในขอบเขตและสิ่งที่ไม่อยู่ในขอบเขต
- `<scope_schema>`: ให้รายละเอียดเชิงโครงสร้างเกี่ยวกับ **หมวดหมู่หลักและหมวดย่อยของคำถามที่ถือว่าอยู่ในขอบเขต** เช่น หัตถการ (เช่น ยาชา), อาการ/ภาวะแทรกซ้อน (เช่น ปวด แผล เลือด), และการปฏิบัติตัวหลังทำหัตถการ (เช่น การใช้หลอด การออกกำลังกาย)
- `<examples_in_scope>`: รวมตัวอย่างคำถามที่ถือว่า **อยู่ในขอบเขต** เพื่อให้คุณเปรียบเทียบกับคำถามใหม่ที่ได้รับ
- `<examples_out_of_scope>`: รวมตัวอย่างคำถามที่ **อยู่นอกขอบเขต** เช่น คำถามทั่วไปเกี่ยวกับฟันโดยไม่เจาะจงช่วงหลังหัตถการ, หรือคำถามที่ไม่เกี่ยวข้องกับทันตกรรมเลย
- `<guideline>`: อธิบาย **หลัก reasoning และเกณฑ์การตัดสินแบบละเอียด** เช่น หากพบคำว่า "ถอนฟัน", "แผล", หรือ "ยาชา" และคำถามมีลักษณะเป็นคำถามหลังการรักษา → ถือว่าอยู่ในขอบเขต  
  แต่หากคำถามไม่ชัดเจน ไม่มีคำหรือบริบทที่เกี่ยวกับหลังหัตถการ → ให้ตอบว่าอยู่นอกขอบเขต
- `<output_format>`: กำหนดรูปแบบผลลัพธ์ที่คุณต้องตอบกลับในรูปแบบ JSON โดยมี 2 ฟิลด์สำคัญ:
  - `out_of_domain`: ระบุว่าอยู่ในขอบเขตหรือไม่ (`true` หรือ `false`)
  - `reason`: ให้เหตุผลแบบสั้น ๆ ว่าทำไมจึงตัดสินเช่นนั้น โดยต้องอิงจากเกณฑ์จริง ไม่ขยายความเอง
- `<examples>`: รวมตัวอย่าง input/output ที่เป็นคำถามจริง พร้อมคำตอบที่ถูกต้องตามหลักการ เพื่อให้คุณใช้เป็นแนวทางในการประเมินคำถามใหม่
                                                              
<task>
คุณคือระบบที่ทำหน้าที่กรองคำถามก่อนส่งต่อให้ผู้ช่วยทันตแพทย์  
หากคำถามไม่เกี่ยวกับ "ทันตกรรมหลังหัตถการ" ต้องปฏิเสธ (out_of_domain: true)

</task>

<context>
ระบบนี้รองรับเฉพาะคำถามที่เกี่ยวข้องกับ **การดูแลหลังหัตถการทางทันตกรรม**  
หัวข้อที่อยู่ในขอบเขต เช่น:
- ถอนฟัน
- ผ่าฟันคุด
- อาการปวด แผล เลือดไหล ฟื้นตัว
- ยาชา ยาแก้ปวด การใช้ยา
- การรับประทานอาหารหลังหัตถการ
- การแปรงฟัน การบ้วนปาก การใช้หลอด
- พฤติกรรมหลังหัตถการโดยรวม
ไม่รวม:
- คำถามทั่วไปที่ไม่เกี่ยวกับฟัน
- คำถามที่ไม่กล่าวถึงช่วงหลังการรักษา
- ข้อความไม่มีความหมาย หรือเป็น noise เช่น "123456", "asdfgh", อีโมจิ ฯลฯ
</context>

<scope_schema>
<หมวดหมู่หลักที่อยู่ในขอบเขต>
- หัตถการ
- อาการ/ภาวะแทรกซ้อน
- การปฏิบัติตัวหลังทำหัตถการ

<หมวดย่อยที่สัมพันธ์>
- หัตถการ:
    - การใช้ยาชา: คำถามเกี่ยวกับชนิด วิธีใช้ ระยะเวลาของฤทธิ์ยาชา
- อาการ/ภาวะแทรกซ้อน:
    - overall, bleeding, pain, wound healing
- การปฏิบัติตัวหลังทำหัตถการ:
    - overall, drinking straw, alcohol, workout, food, oral hygiene
</scope_schema>

<examples_in_scope>
- ปวดหลังถอนฟันทำไงดี
- แผลถอนฟันหายกี่วัน
- ถอนฟันแล้วใช้หลอดได้ไหม
- ยาชาถอนฟันจะอยู่ได้นานกี่ชั่วโมง
- ยาชาจะหมดฤทธิ์เมื่อไหร่
</examples_in_scope>

<examples_out_of_scope>
- ฟันเหลืองเกิดจากอะไร
- อาหารเพื่อสุขภาพ
- จะลงทุนอะไรดี
- ws;vgg?
- 🙃🙃🙃
</examples_out_of_scope>

<guideline>
วิเคราะห์แบบ Reasoning:
1. คำว่า "ถอนฟัน" → เกี่ยวกับหัตถการ
2. คำว่า "อาการผิดปกติ" → เชื่อมโยงกับอาการ/ภาวะแทรกซ้อน
3. คำว่า "ควรกลับไปพบทันตแพทย์" → มีบริบทหลังการรักษา
→ สรุป: อยู่ในขอบเขต (false)

เกณฑ์ตัดสิน:
- ถ้า **เข้าใจได้** และเกี่ยวข้องกับหัวข้อใน `<scope_schema>` → `out_of_domain: false`
- ถ้าไม่เกี่ยวกับทันตกรรมหรือเป็นข้อความไร้ความหมาย → `out_of_domain: true`
- หากข้อความเกี่ยวข้องกับ "ชีวิตประจำวัน", "การท่องเที่ยว", "อาหารทั่วไป", หรือ "การลงทุน" → ต้องตอบว่า out_of_domain: true
- หากข้อความไม่มีคำที่เกี่ยวข้องกับทันตกรรม หรือบริบทหลังการรักษา → ต้องตอบว่า out_of_domain: true
**ห้ามเดา ห้ามขยายความ ให้ตัดสินจากข้อความตรง ๆ เท่านั้น**
- คำที่มักพบในคำถามที่อยู่ในขอบเขต: "ถอนฟัน", "ผ่าฟันคุด", "ยาชา", "ปวด", "แผล", "เลือด", "ผิดปกติ", "พบทันตแพทย์", "หลังหัตถการ" หากมีคำเหล่านี้ร่วมกับบริบทที่เป็นคำถาม → ถือว่าอยู่ในขอบเขต
</guideline>

<output_format>
{
  "out_of_domain": true | false,
  "reason": "อธิบายสั้น ๆ เช่น มีคำว่า 'ถอนฟัน' และ 'ยาชา' จึงอยู่ในขอบเขต"
}
</output_format>
<examples>                      
[IN] หลังถอนฟัน อาการผิดปกติแบบไหนที่ควรกลับไปพบทันตแพทย์  
[OUT] {"out_of_domain": false, "reason": "มีคำว่า 'หลังถอนฟัน' และ 'อาการผิดปกติ' จึงอยู่ในขอบเขต"}
[IN] หลังถอนฟันอาการผิดปกติแบบไหนที่ควรกลับไปพบทันตแพทย์  
[OUT] {"out_of_domain": false, "reason": "กล่าวถึงอาการผิดปกติหลังถอนฟัน จึงอยู่ในขอบเขต"}
                      
งที่คุณต้องทำ:
1. อ่านคำถามจากผู้ใช้
2. ใช้ข้อมูลจาก `<criteria>`, `<scope_schema>`, `<guideline>` และ `<examples>` เพื่อพิจารณา
3. ตอบกลับด้วย JSON ตาม `<output_format>` โดยไม่ขยายความหรือเดาเพิ่มเติม                      
"""),
        HumanMessagePromptTemplate.from_template(
            "คำถาม: {user_query}\nโปรดวิเคราะห์ตามขั้นตอน reasoning และตอบกลับเป็น JSON ตาม <output_format>"
        )
    ])
    chain = prompt | llm
    return chain.invoke({"user_query": user_query})


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

# ✅ รวมทุกขั้นตอนเป็น pipeline
def run_classification_pipeline(state: AgentState) -> AgentState:
    latency_info = {}
    
    #เตรียม query ที่มีบริบทเดิมรวมอยู่ (กรณี follow-up)
    merged_query = (
        "\n".join(state.previous_turns + [state.user_query])
        if state.previous_turns else state.user_query
    )
    print("🚦 Step 1: Out-of-Domain Check")
    start = time.perf_counter()
    ood_result = check_out_of_domain(state.user_query)
    print("✅ Out-of-Domain Result:", ood_result)
    if ood_result is None or ood_result.out_of_domain is None:
        state.classification_result.out_of_domain = True
        state.response = "ไม่สามารถประมวลผลคำถามได้"
        state.latency = latency_info
        return state
    latency_info["out_of_domain"] = round(time.perf_counter() - start, 3)
    latency_info["tokens_out_of_domain"] = count_tokens(state.user_query, model=TOGETHER_MODEL)
    state.classification_result.out_of_domain = ood_result.out_of_domain
    state.classification_result.out_of_domain_reason = ood_result.reason
    if state.should_terminate():
        state.latency = latency_info
        return state

    print("🔍 Step 2: Clarity Check")
    start = time.perf_counter()
    clarity_result = check_clarity(state.user_query)
    print("✅ Clarity Result:", clarity_result)
    latency_info["clarification"] = round(time.perf_counter() - start, 3)
    latency_info["tokens_clarification"] = count_tokens(state.user_query, model=TOGETHER_MODEL)
    state.classification_result.clarification_needed = clarity_result.clarification_needed
    state.classification_result.clarification_reason= clarity_result.reason
    if state.should_terminate():
        state.latency = latency_info
        return state

    print("📊 Step 3: Category Classification")
    start = time.perf_counter()
    category_result = classify_categories(state.user_query)
    latency_info["classification"] = round(time.perf_counter() - start, 3)
    latency_info["tokens_classification"] = count_tokens(state.user_query, model=TOGETHER_MODEL)
    state.classification_result.category_level_1 = category_result.category_level_1
    state.classification_result.category_level_2 = category_result.category_level_2
    state.latency = latency_info
    return state
