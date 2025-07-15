# Out of domain OpenAI llm grail Date 14/7
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- ตรวจ Out-of-Domain ด้วย Guardrails [Guardrails ของ OpenAI Agents](https://openai.github.io/openai-agents-python/guardrails/) โดย integrate ใช้รวมกับ clarification และ classification (langgrah เดิม)
  - ปรับเอา guardail ออกมานอก graph (เช็ค query ด้วย guardail ก่อนเข้า graph) ต่างจาก [guardail ใน ไฟล์นี้](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_openAI/main_graph.py) ที่ guardail 	อยู่ ใน Graph
- เชื่อมกับ open webui
- pipeline: check Out-of-Domain ด้วย Guardrails จาก OpenAI -> check clarification -> check classification
- Entry Point ของ Graph คือ classify_query function 
## ปัญหา/แก้เพิ่ม
- ปรับ format json [main.py](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_openAI_llm_grail/main.py)
- สร้าง diagram เพื่อให้เห็นภาพการเชื่อมต่อ open ui 

### 1. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่

**Test Case:**  
[question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_clari_test.xlsx)

**Output:**  
[Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI_llm_grail/test_case/results_clari_11_7.xlsx)
<img width="1212" height="906" alt="image" src="https://github.com/user-attachments/assets/8bf560ba-f5eb-4ff2-829e-509b072da6dc" />


---
### 2. ตรวจสอบว่า Query เป็นคำถาม out 0f domain หรือไม่ (test cases ใหม่: query ที่ดู out of domain ชัดเจน)


**Test Case:**  
[question_outofdomain_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI_llm_grail/test_case/outofdomain_results_11_7.xlsx)

<img width="1389" height="735" alt="image" src="https://github.com/user-attachments/assets/61b403ac-c593-4277-9a0d-5d35bd4c757a" />



---

### 3. ตรวจสอบว่า Query ถูกแยก Category ตรงตาม Expected หรือไม่



**Test Case:**  
[question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_2categorylevel.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/outOfDomain_openAI_llm_grail/test_case/question_2categorylevel.xlsx)
<img width="1534" height="680" alt="image" src="https://github.com/user-attachments/assets/eb662b59-0503-4f95-8b2f-72a5ef0e6832" />



