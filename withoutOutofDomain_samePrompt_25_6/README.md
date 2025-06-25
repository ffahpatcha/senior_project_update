![output_classi](https://github.com/user-attachments/assets/91373f40-cb46-4ddf-978d-789db43add97)# Senior Project Date 25/6
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- \agents\query_classification_agent.py
  - ปรับเอาส่วนเช็ค out of domain จาก query ออก [query_classification_agent.py (lines 54–170)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L54-L170)
  - ใช้ llm 2 ตัวในการแยก clarification_needed,classify_categories (จากเดิม llm 3 ตัว)
  - prompt ในส่วน clarification_needed,classify_categories ยังคงเหมือนเดิมกับ version [query_classification_agent.py (lines 174–400)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L174-L400)

## ปัญหา/แก้เพิ่ม
- output จาก test case(เดิม) [question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_2categorylevel.xlsx) พบว่า llm ให้ result ตรงตาม expected ทั้งหมด
- ได้ทดลองเพิ่มเติมโดยเพิ่ม test case  [question_outofdomain_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx.xlsx) ที่เห็นชัดว่าเป็น out of domain ชัดเจน มาทดลอง พบว่ายังมี 2 case ที่ไม่ตรงตาม expected

## ผลลัพธ์

- เช็คว่า query นั้นจำเป็นต้อง clarify เพิ่มตาม expected หรือไม่  
  Test Case: [question_clari_test.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_clari_test.xlsx)  
  Output: [Clarification_result.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/output/results_clari_without_outofdomain.xlsx)  
  ![output_clari](https://github.com/user-attachments/assets/aa0e3235-e478-48ff-b5ed-d9e86dd2bb6e)

- เช็คว่า query นั้นถูกแยก category ตรงตาม expected หรือไม่  
  Test Case: [question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_2categorylevel.xlsx)  
  Output: [Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/output/results25_6.xlsx)  
  ![output_classi](https://github.com/user-attachments/assets/e08eeb0b-ed43-458f-8021-c59f1a018ed6)

- เช็คว่า query นั้นถูกจัดว่าเป็น query out of domain ตาม expected หรือไม่  
  Test Case(ใหม่): [question_2categorylevel.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/question_outofdomain_test.xlsx)  
  Output: [Classification_Results.xlsx](https://raw.githubusercontent.com/ffahpatcha/senior_project_update/main/withoutOutofDomain_samePrompt_25_6/test_case/output/results_testout_without_outofdomain.xlsx)  
  ![output_clari_new_test_case](https://github.com/user-attachments/assets/cf109945-8001-42fb-92d5-8f0f1fbee405)

