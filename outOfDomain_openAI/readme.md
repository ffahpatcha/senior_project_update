# Out of domain OpenAI Date 2/7
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- ตรวจ Out-of-Domain ด้วย Guardrails [Guardrails ของ OpenAI Agents](https://openai.github.io/openai-agents-python/guardrails/) โดย integrate ใช้รวมกับ clarification และ classification (langgrah เดิม)
  - ปรับเอา function ตรวจ out of domain เดิมออก นำ dental_guardrail_agent มาใช้ตรวจ out of domain แทน 
  - ส่วนของ prompt ของ dental_guardrail_agent [dental_guardrail_agent.py](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_openAI/my_agents/dental_guardrail_agent.py) มาจาก [query_classification_agent.py (บรรทัด 61–164)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L61-L164)
- pipeline: check Out-of-Domain ด้วย Guardrails จาก OpenAI -> check clarification -> check classification

## ปัญหา/แก้เพิ่ม
- พอมาใช้จริงส่วนของ out of domain กับ clarification_needed ยังมีส่วนที่ intercept กันอยู่
- ปรับลองเอา out of domain เอก เพื่อดูว่าส่วน calrification_needed จะให้ผลลออกมายังไงบ้าง

## ผลลัพธ์

### 1. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่

ผลลัพธ์พบว่าทุก test cases เป็นไปตาม expected

**Test Case:**  
[question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_clari_test.xlsx)

**Output:**  
[Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/results_clari_outOfDomain_openAI.xlsx)


---
### 2. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่ (test cases ใหม่: query ที่ดู out of domain ชัดเจน)

พบว่ายังมี 2 case ที่ยังไม่ถูกต้องตาม expected

**Test Case:**  
[question_outofdomain_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/evaluation_results.csv)



---

### 3. ตรวจสอบว่า Query ถูกแยก Category ตรงตาม Expected หรือไม่

**การแยกหมวดหมู่หลัก (Level 1):**

- พบว่า **2 cases** แยกไม่ตรงตาม expected เป็น query เดียวกันกับในรอบก่อน
- และ **2 cases**  ที่เกิด clarification_needed=True

**การแยกหมวดหมู่ย่อย (Level 2):**

- พบว่า **2 cases** แยกไม่ตรงตาม expected  เป็น query เดียวกันกับในรอบก่อน ([ดูรายละเอียดผลลัพธ์เดิม](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStruture_Output_11_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C))
- และ **2 cases** ที่เกิด clarification_needed=True

**Test Case:**  
[question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_2categorylevel.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/results_outOfDomain_openAI.xlsx


