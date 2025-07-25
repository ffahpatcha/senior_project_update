# Out of domain OpenAI Date 2/7
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- ตรวจ Out-of-Domain ด้วย Guardrails [Guardrails ของ OpenAI Agents](https://openai.github.io/openai-agents-python/guardrails/) โดย integrate ใช้รวมกับ clarification และ classification (langgrah เดิม)
  - ปรับเอา function ตรวจ out of domain เดิมออก นำ dental_guardrail_agent มาใช้ตรวจ out of domain แทน 
  - ส่วนของ prompt ของ dental_guardrail_agent [dental_guardrail_agent.py](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_openAI/my_agents/dental_guardrail_agent.py) มาจาก [query_classification_agent.py (บรรทัด 61–164)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L61-L164)
- pipeline: check Out-of-Domain ด้วย Guardrails จาก OpenAI -> check clarification -> check classification

## ปัญหา/แก้เพิ่ม
- openAI ต้องมี credit เสียตัง
- ปรับ code ให้เป็นระเบียบขึ้น
- ปรับ prompt ของ dental_guardrail_agent เพิ่มเติม เนื่องจากมี case ที่ตรวจสอบว่า Query เป็นคำถาม out 0f domain หรือไม่ พบว่า คำถามว่า "ช่วยแต่ง caption ให้รูปนี้หน่อย" พบว่า out_of_domain = false 

## ผลลัพธ์

### 1. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่

ผลลัพธ์พบว่ามี 3  test cases ที่ไม่เป็นไปตาม expected ว่าควรที่จะ clarification เพิ่ม 
- ทั้ง 3 case พบว่า out_of_domain = true

**Test Case:**  
[question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_clari_test.xlsx)

**Output:**  
[Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/results_clari_outOfDomain_openAI.xlsx)
<img width="1350" height="595" alt="image" src="https://github.com/user-attachments/assets/fe647eb5-71ea-4562-bb92-e35066e7e64b" />


---
### 2. ตรวจสอบว่า Query เป็นคำถาม out 0f domain หรือไม่ (test cases ใหม่: query ที่ดู out of domain ชัดเจน)

พบว่ายังมี 1 case ที่ยังไม่ถูกต้องตาม expected ว่าควรที่จะ out of domain เป็น true 
เมื่อตรวจ Out-of-Domain ด้วย Guardrails openAI พบว่าระบบให้เหตุผลของ out_of_domain ได้ดี[reasoning out of domain column E](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/evaluation_results.xlsx)

**Test Case:**  
[question_outofdomain_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/evaluation_results.xlsx)
<img width="2222" height="986" alt="image" src="https://github.com/user-attachments/assets/67e18bcb-388c-42ee-9a28-c5fd063a46eb" />



---

### 3. ตรวจสอบว่า Query ถูกแยก Category ตรงตาม Expected หรือไม่

- พบว่า **1 cases** แยกไม่ตรงตาม expected  เป็น query เดียวกันกับในรอบก่อน ([ดูรายละเอียดผลลัพธ์เดิม](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStruture_Output_11_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C))
- และ **1 cases** ที่เกิด clarification_needed=True
  
ผลลัพธ์พัฒนาในทางที่ดีขึ้น 

**Test Case:**  
[question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_2categorylevel.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/results_outOfDomain_openAI.xlsx)
<img width="2163" height="918" alt="image" src="https://github.com/user-attachments/assets/9ff734b9-5682-480f-bdb2-83550ed4d4d3" />


