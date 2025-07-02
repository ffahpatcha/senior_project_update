# outOfDomain_google_error Date 2/7
ปรับ classification agent ต่อ

## Folders ที่มีการปรับหลัก
- ลองเพิ่มขั้นตอน **Delegation for Greetings & Farewells** เพื่อให้ Agent สามารถแบ่งหน้าที่ตอบคำทักทายและคำอำลาได้อัตโนมัติ [ดูขั้นตอนอย่างละเอียดที่นี่](https://google.github.io/adk-docs/tutorials/agent-team/#step-2-going-multi-model-with-litellm-optional)
  - สร้าง agent Greeting Agent , Farewell Agent  [greeting_farewell_agents.py](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_google_error/agents/greeting_farewell_agents.py)
  - pipeline ใหม่ คือตรวจสอบว่าคำถามมีคำทักทายหรือคำอำลาหรือไม่ก่อน จากนั้นตามด้วย check_clarification -> check out of domain -> classification [query_classification_agent.py (บรรทัด 408–459)](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_google_error/agents/query_classification_agent.py#L408-L459)
- \agents\query_classification_agent.py
  - ใช้ llm 3 ตัวในการแยก out of domain,clarification_needed,classify_categories เหมือน [pipeline_v2_clarity_first_25_6](https://github.com/ffahpatcha/senior_project_update/tree/main/pipeline_v2_clarity_first_25_6)

## ปัญหา/แก้เพิ่ม
- error เข้าใจว่าเป็นเพราะ builder.add_node() ของ StateGraph รองรับแค่ Runnable,Callable,dict แต่ที่ใส่ไป (greeting_agent) เป็น LlmAgent จาก google.adk.agents.llm_agent.LlmAgent ซึ่ง ไม่ได้แปลงเป็น Runnable อัตโนมัติ เลยทำให้ LangGraph โยน TypeError ออกมา
  ![image](https://github.com/user-attachments/assets/4c1c34df-d297-4f22-aae3-47b28e6d56b0)

