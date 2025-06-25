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
