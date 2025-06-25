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

ผลลัพธ์พบว่าทุก test cases เป็นไปตาม expected

**Test Case:**  
[question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/question_clari_test.xlsx)

**Output:**  
[Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/results_cali_pipeline_v2_clarity_first.xlsx)

![output_clari](https://github.com/user-attachments/assets/88e2cf36-1172-4514-800d-59d0ba401762)

---
### 2. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่ (test cases ใหม่: query ที่ดู out of domain ชัดเจน)

พบว่ายังมี 2 case ที่ยังไม่ถูกต้องตาม expected

**Test Case:**  
[question_outofdomain_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/results_cali_pipeline_v2_clarity_first_out_of_domain.xlsx)
![output_clari_outofdomain](https://github.com/user-attachments/assets/9fab2d9b-3ca0-42b3-b542-027d19b3f694)


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
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/pipeline_v2_clarity_first_25_6/test_case/results_pipeline_v2_clarity_first.xlsx)
![output_classi](https://github.com/user-attachments/assets/33e59091-8a89-43fe-9131-5d34a6c58b0c)



