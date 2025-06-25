# Senior Project Date 11/6
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- \agents\query_classification_agent.py
  - ปรับเป็นใช้ llm 3 ตัวในการแยก out of domain,clarification_needed,classify_categories
    ![workflow2-Page-16 drawio (1)](https://github.com/user-attachments/assets/0c827799-dca4-418d-923f-7f9f2c44d8b5)
  - ปรับ prompt ให้ครอบคลุม use case ของแต่ละส่วนข้างต้น
  - ปรับโครงสร้าง prompt ให้มีการใช้ XML 
- \utils\llm_utils.py โดยปรับให้ output จาก llm มี structured_output_schema และเป็น Pydantic schema
- main_graph.py
- state_schema.py

## ปัญหา/แก้เพิ่ม
- latency llm 3 ตัวทำให้ latency เพิ่ม
- prompt clarification ต้องครอบคลุมมากกว่านี้ (คนที่ถามมาจะต้องบอกอาการตัวเองก่อน)
    https://furry-brownie-a7d.notion.site/11-6-2162b0daf61f807eaa1ddc59b7a7870e?source=copy_link
  - ก่อนโครงสร้าง XML ปรับว่ามันคืออะไร

## ผลลัพธ์

### 1. ตรวจสอบว่า Query จำเป็นต้อง Clarify เพิ่มเติมหรือไม่

ผลลัพธ์พบว่า มี **13 cases** ที่ไม่เป็นคำถามที่ต้องการ clarify เพิ่มเติม  

**Test Case:**  
[question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/seniorProject_withStruture_Output_11_6/test_case/question_clari_test.xlsx)

**Output:**  
[Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/seniorProject_withStruture_Output_11_6/test_case/output/results_clari.xlsx)

![output_clari](https://github.com/user-attachments/assets/a9145a4f-eabb-4b75-b21b-a576e9484b64)




---

### 2. ตรวจสอบว่า Query ถูกแยก Category ตรงตาม Expected หรือไม่

**การแยกหมวดหมู่หลัก (Level 1):**

- พบว่า **2 cases** แยกไม่ตรงตาม expected 
- และ **1 cases** ระบบเกิด error

**การแยกหมวดหมู่ย่อย (Level 2):**

- พบว่า **2 cases** แยกไม่ตรงตาม expected  
- และ **1 cases** ระบบเกิด error   

**Test Case:**  
[question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/seniorProject_withStruture_Output_11_6/test_case/question_2categorylevel.xlsx)

**Output:**  
[Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/seniorProject_withStruture_Output_11_6/test_case/output/category_classi_result.xlsx)

![Classification Output](https://github.com/user-attachments/assets/2712d464-b016-4a9c-91da-517c2920e77d)





