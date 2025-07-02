## ลำดับ

- [**seniorProject_withoutStructure_Output_7_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withoutStructure_Output_7_6)  
  - ปรับ `prompt` ของ `classification agent` โดยยัง **ไม่มี structure output** และใช้ **LLM ตัวเดียว** ในการจัดกลุ่มคำถาม

- [**seniorProject_withStructure_Output_11_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStruture_Output_11_6)  
  - ปรับ `prompt` ของ `classification agent` ให้มี **structure output** และใช้ **LLM 3 ตัว** ในการจัดกลุ่มคำถาม
  - สรุปผล [result](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStruture_Output_11_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C)
  
- [**seniorProject_withoutStructure_Output_18_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withoutStructure_Output_18_6)  
  - ปรับ `prompt` ของส่วน `clarify_needed` ให้มีความ **ครอบคลุมมากขึ้น**
  - สรุปผล [result](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withoutStructure_Output_18_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C)

- [**withoutOutofDomain_samePrompt_25_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/withoutOutofDomain_samePrompt_25_6)  
  - **ตัดส่วนการแยก out_of_domain ออก** โดยที่ `prompt` ของ `clarify_needed` และ `classification category` ยังคง **เหมือนเดิม**
  - ปรับเอาส่วนเช็ค out of domain จาก query ออก [query_classification_agent.py (lines 54–170)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L54-L170)
  - สรุปผล [result](https://github.com/ffahpatcha/senior_project_update/blob/main/withoutOutofDomain_samePrompt_25_6/README.md#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C)

- [**pipeline_v2_clarity_first_25_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/pipeline_v2_clarity_first_25_6)  
  - ใช้ llm 3 ตัวในการแยก out of domain,clarification_needed,classify_categories แต่มีการปรับลำดับ pipeline ให้มีการเช็ค clarification เริ่มก่อน
  - prompt ในแต่ละส่วนเหมือน  [seniorProject_withoutStructure_Output_18_6](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py)

  - สรุปผล [result](https://github.com/ffahpatcha/senior_project_update/tree/main/pipeline_v2_clarity_first_25_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C)


- [**outOfDomain_google_error_2_7**](https://github.com/ffahpatcha/senior_project_update/tree/main/outOfDomain_google_error)
  - ลองเพิ่มขั้นตอน **Delegation for Greetings & Farewells** เพื่อให้ Agent สามารถแบ่งหน้าที่ตอบคำทักทายและคำอำลาได้อัตโนมัติ [ดูขั้นตอนอย่างละเอียดที่นี่](https://google.github.io/adk-docs/tutorials/agent-team/#step-2-going-multi-model-with-litellm-optional)
    - สร้าง agent Greeting Agent , Farewell Agent  [greeting_farewell_agents.py](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_google_error/agents/greeting_farewell_agents.py)
    - pipeline ใหม่ คือตรวจสอบว่าคำถามมีคำทักทายหรือคำอำลาหรือไม่ก่อน จากนั้นตามด้วย check_clarification -> check out of domain -> classification [query_classification_agent.py (บรรทัด 408–459)](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_google_error/agents/query_classification_agent.py#L408-L459)
  - ผล error
    
- [**Out of domain OpenAI_2_7**](https://github.com/ffahpatcha/senior_project_update/tree/main/outOfDomain_openAI)
  - ตรวจ Out-of-Domain ด้วย Guardrails [Guardrails ของ OpenAI Agents](https://openai.github.io/openai-agents-python/guardrails/) โดย integrate ใช้รวมกับ clarification และ classification (langgrah เดิม)
    - ปรับเอา function ตรวจ out of domain เดิมออก นำ dental_guardrail_agent มาใช้ตรวจ out of domain แทน 
    - ส่วนของ prompt ของ dental_guardrail_agent [dental_guardrail_agent.py](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_openAI/my_agents/dental_guardrail_agent.py) มาจาก [query_classification_agent.py (บรรทัด 61–164)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L61-L164)
  - สรุปผล [result](https://github.com/ffahpatcha/senior_project_update/tree/main/outOfDomain_openAI#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C)
