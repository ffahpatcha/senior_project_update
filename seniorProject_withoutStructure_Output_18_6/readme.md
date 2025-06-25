# Senior Project Date 18/6
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- \agents\query_classification_agent.py
  - ใช้ llm 3 ตัวในการแยก out of domain,clarification_needed,classify_categories เหมือน 11/6
  - ปรับ prompt ส่วน clarification_needed ให้ครอบคลุมมากขึ้น
- main_graph.py
- state_schema.py

## ปัญหา/แก้เพิ่ม
- พอมาใช้จริงส่วนของ out of domain กับ clarification_needed ยังมีส่วนที่ intercept กันอยู่
- ปรับลองเอา out of domain เอก เพื่อดูว่าส่วน calrification_needed จะให้ผลลออกมายังไงบ้าง

## ผลลัพธ์

- เช็คว่า query นั้นจำเป็นต้อง clarify เพิ่มตาม expected หรือไม่  
  Test Case: [question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/seniorProject_withoutStructure_Output_18_6/test_case/question_clari_test.xlsx)  
  Output: [Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/seniorProject_withoutStructure_Output_18_6/test_case/output/results_clari3.xlsx)  
  ![output_clari](https://github.com/user-attachments/assets/dd42081c-054b-4ba5-a9c8-9c303805dffd)



- เช็คว่า query นั้นถูกแยก category ตรงตาม expected หรือไม่  
  Test Case: [question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/seniorProject_withoutStructure_Output_18_6/test_case/question_2categorylevel.xlsx)  
  Output: [Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/seniorProject_withoutStructure_Output_18_6/test_case/output/result4.xlsx)  
  ![output_classi](https://github.com/user-attachments/assets/0033ecfa-f2d3-401e-ac76-4f890d1ed5dd)

