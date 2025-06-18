# Senior Project Date 11/6
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- \agents\query_classification_agent.py
  - ปรับเป็นใช้ llm 3 ตัวในการแยก out of domain,clarification_needed,classify_categories
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
