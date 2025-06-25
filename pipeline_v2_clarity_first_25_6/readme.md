# pipeline_v2_clarity_first_25_6 Date 25_6
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- \agents\query_classification_agent.py
  - ใช้ llm 3 ตัวในการแยก out of domain,clarification_needed,classify_categories แต่มีการปรับลำดับ pipeline ให้มีการเช็ค clarification เริ่มก่อน
    ![workflow2-Copy of Page-16 drawio](https://github.com/user-attachments/assets/47048245-7046-422f-b858-542b5d88ef61)
  - prompt ในแต่ละส่วนเหมือน [seniorProject_withoutStructure_Output_18_6](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withoutStructure_Output_18_6)

## ปัญหา/แก้เพิ่ม
- พอมาใช้จริงส่วนของ out of domain กับ clarification_needed ยังมีส่วนที่ intercept กันอยู่
- ปรับลองเอา out of domain เอก เพื่อดูว่าส่วน calrification_needed จะให้ผลลออกมายังไงบ้าง

## ผลลัพธ์

### 1. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่

ผลลัพธ์พบว่า มี **9 cases** ที่ไม่เป็นคำถามที่ต้องการ clarify เพิ่มเติม  
เมื่อพิจารณาสาเหตุที่ไม่ตรงตาม expected พบว่า query เหล่านั้นถูกจัดว่าเป็น **out_of_domain**

**Test Case:**  
[question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_clari_test.xlsx)

**Output:**  
[Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/results_cali_pipeline_v2_clarity_first.xlsx)

![Clarification Output](https://github.com/user-attachments/assets/dd42081c-054b-4ba5-a9c8-9c303805dffd)

---

### 2. ตรวจสอบว่า Query ถูกแยก Category ตรงตาม Expected หรือไม่

**การแยกหมวดหมู่หลัก (Level 1):**

- พบว่า **2 cases** แยกไม่ตรงตาม expected เป็น query เดียวกันกับที่เคยเกิดปัญหาในรอบก่อน 
- และ **3 cases** ระบบเกิด error

**การแยกหมวดหมู่ย่อย (Level 2):**

- พบว่า **2 cases** แยกไม่ตรงตาม expected  
- และ **3 cases** ระบบเกิด error   
- โดย **2 cases ที่ error** เป็น query เดียวกันกับที่เคยเกิดปัญหาในรอบก่อน  
  ([ดูรายละเอียดผลลัพธ์เดิม](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStruture_Output_11_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C))

**Test Case:**  
[question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_2categorylevel.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/results_pipeline_v2_clarity_first.xlsx)

![Classification Output](https://github.com/user-attachments/assets/0033ecfa-f2d3-401e-ac76-4f890d1ed5dd)

