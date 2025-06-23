# Senior Project Date 7/6
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- \agents\query_classification_agent.py
  - ใช้ llm 1 ตัวในการแยก out of domain,clarification_needed,classify_categories โดยการ prompt 
  - ให้ output ออกมาเป็น json ผ่านการให้ตัวอย่าง prompt ลักษณะของ json ที่ต้องการเข้าไป
- \utils\llm_utils.py output จาก llm ยังไม่มี structured_output_schema และเป็น Pydantic schema
- main_graph.py
- state_schema.py

## ปัญหา/แก้เพิ่ม
- ต้องแก้ prompt เพิ่มเติม
- output json บางอันออกมาไม่เป็นไปตามที่ต้องการ
![image](https://github.com/user-attachments/assets/29de8be9-111d-44f9-a7d3-7bb36ca7be54)

