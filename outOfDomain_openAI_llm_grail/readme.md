# Out of domain OpenAI llm grail Date 14/7
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- ตรวจ Out-of-Domain ด้วย Guardrails [Guardrails ของ OpenAI Agents](https://openai.github.io/openai-agents-python/guardrails/) โดย integrate ใช้รวมกับ clarification และ classification (langgrah เดิม)
  - ปรับเอา guardail ออกมานอก graph (เช็ค query ด้วย guardail ก่อนเข้า graph) ต่างจาก [guardail ใน ไฟล์นี้](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_openAI/main_graph.py) ที่ guardail 	อยู่ ใน Graph
- pipeline: check Out-of-Domain ด้วย Guardrails จาก OpenAI -> check clarification -> check classification
- Entry Point ของ Graph คือ classify_query function 
## ปัญหา/แก้เพิ่ม
- ปรับ prompt ของ dental_guardrail_agent เพิ่มเติม เนื่องจากมี case ที่ตรวจสอบว่า Query เป็นคำถาม out 0f domain หรือไม่ พบว่า คำถามว่า "ช่วยแต่ง caption ให้รูปนี้หน่อย" พบว่า out_of_domain = false 
- เมื่อ Tripwire Triggered API Endpoint ตอบ JSON เลย ไม่รัน graph [main.py](outOfDomain_openAI_llm_grail/main.py)
## ผลลัพธ์

### 1. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่

ผลลัพธ์พบว่ามี 3  test cases ที่ไม่เป็นไปตาม expected ว่าควรที่จะ clarification เพิ่ม 
- ทั้ง 3 case พบว่า out_of_domain = true

**Test Case:**  
[question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_clari_test.xlsx)

**Output:**  
[Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/results_clari_outOfDomain_openAI.xlsx)
<img width="1212" height="906" alt="image" src="https://github.com/user-attachments/assets/8bf560ba-f5eb-4ff2-829e-509b072da6dc" />


---
### 2. ตรวจสอบว่า Query เป็นคำถาม out 0f domain หรือไม่ (test cases ใหม่: query ที่ดู out of domain ชัดเจน)

พบว่ายังมี 1 case ที่ยังไม่ถูกต้องตาม expected ว่าควรที่จะ out of domain เป็น true 
เมื่อตรวจ Out-of-Domain ด้วย Guardrails openAI พบว่าระบบให้เหตุผลของ out_of_domain ได้ดี[reasoning out of domain column E](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/evaluation_results.xlsx)

**Test Case:**  
[question_outofdomain_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/evaluation_results.xlsx)

<img width="1389" height="735" alt="image" src="https://github.com/user-attachments/assets/61b403ac-c593-4277-9a0d-5d35bd4c757a" />



---

### 3. ตรวจสอบว่า Query ถูกแยก Category ตรงตาม Expected หรือไม่

- พบว่า **1 cases** แยกไม่ตรงตาม expected  เป็น query เดียวกันกับในรอบก่อน ([ดูรายละเอียดผลลัพธ์เดิม](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStruture_Output_11_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C))
- และ **1 cases** ที่เกิด clarification_needed=True
  
ผลลัพธ์พัฒนาในทางที่ดีขึ้น 

**Test Case:**  
[question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_2categorylevel.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI/test_case/results_outOfDomain_openAI.xlsx)
<img width="1534" height="680" alt="image" src="https://github.com/user-attachments/assets/eb662b59-0503-4f95-8b2f-72a5ef0e6832" />



