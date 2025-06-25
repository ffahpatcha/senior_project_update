# Senior Project Date 25/6
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- \agents\query_classification_agent.py
  - ปรับเอาส่วนเช็ค out of domain จาก query ออก [query_classification_agent.py (lines 54–170)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L54-L170)
  - ใช้ llm 2 ตัวในการแยก clarification_needed,classify_categories (จากเดิม llm 3 ตัว)
  - prompt ในส่วน clarification_needed,classify_categories ยังคงเหมือนเดิมกับ version [query_classification_agent.py (lines 174–400)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L174-L400)

## ปัญหา/แก้เพิ่ม
- output จาก test case(เดิม) [question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_2categorylevel.xlsx) พบว่า llm ให้ result ตรงตาม expected ทั้งหมด
- ได้ทดลองเพิ่มเติมโดยเพิ่ม test case  [question_outofdomain_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx) ที่เห็นชัดว่าเป็น out of domain ชัดเจน มาทดลอง พบว่ายังมี 2 case ที่ไม่ตรงตาม expected

## ผลลัพธ์

### 1. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่
  ผลลัพธ์พบว่าทุก test cases เป็นไปตาม expected
  
**Test Case:**  
[question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_clari_test.xlsx)

**Output:**  
[Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/output/results_clari_without_outofdomain.xlsx)

![Clarification Output](https://github.com/user-attachments/assets/aa0e3235-e478-48ff-b5ed-d9e86dd2bb6e)

---

### 2. ตรวจสอบว่า Query ถูกแยก Category ตรงตาม Expected หรือไม่

**การแยกหมวดหมู่หลัก (Level 1):**

- พบว่า **2 cases** แยกไม่ตรงตาม expected เป็น query เดียวกันกับที่เคยเกิดปัญหาในรอบก่อน 
- และ **3 cases** ระบบเกิด error

**การแยกหมวดหมู่ย่อย (Level 2):**

- พบว่า **2 cases** แยกไม่ตรงตาม expected  
- และ **3 cases** ระบบเกิด error   
- โดย **2 cases ที่ error** เป็น query เดียวกันกับที่เคยเกิดปัญหาในรอบก่อน  เนื่องจากยังไม่ได้ปรับ prompt
  ([ดูรายละเอียดผลลัพธ์เดิม](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStruture_Output_11_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C))
  
**Test Case:**  
[question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_2categorylevel.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/output/results25_6.xlsx)

![Classification Output](https://github.com/user-attachments/assets/e08eeb0b-ed43-458f-8021-c59f1a018ed6)

---

### 3. ตรวจสอบว่า Query ถูกจัดว่าเป็น Out of Domain ตาม Expected หรือไม่

พบว่ายังมี 2 case ที่ยังไม่ถูกต้องตาม expected

**Test Case:**  
[question_outofdomain_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/output/results_testout_without_outofdomain.xlsx)

![Out of Domain Output](https://github.com/user-attachments/assets/cf109945-8001-42fb-92d5-8f0f1fbee405)

