## ลำดับ

- [**seniorProject_withoutStructure_Output_7_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withoutStructure_Output_7_6)  
  - ปรับ `prompt` ของ `classification agent` โดยยัง **ไม่มี structure output** และใช้ **LLM ตัวเดียว** ในการจัดกลุ่มคำถาม

- [**seniorProject_withStructure_Output_11_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStructure_Output_11_6)  
  - ปรับ `prompt` ของ `classification agent` ให้มี **structure output** และใช้ **LLM 3 ตัว** ในการจัดกลุ่มคำถาม
  - สรุปผล [result](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withStruture_Output_11_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C)
  
- [**seniorProject_withoutStructure_Output_18_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withoutStructure_Output_18_6)  
  - ปรับ `prompt` ของส่วน `clarify_needed` ให้มีความ **ครอบคลุมมากขึ้น**
  - สรุปผล [result](https://github.com/ffahpatcha/senior_project_update/tree/main/seniorProject_withoutStructure_Output_18_6#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C)

- [**withoutOutofDomain_samePrompt_25_6**](https://github.com/ffahpatcha/senior_project_update/tree/main/withoutOutofDomain_samePrompt_25_6)  
  - **ตัดส่วนการแยก out_of_domain ออก** โดยที่ `prompt` ของ `clarify_needed` และ `classification category` ยังคง **เหมือนเดิม**
  - ปรับเอาส่วนเช็ค out of domain จาก query ออก [query_classification_agent.py (lines 54–170)](https://github.com/ffahpatcha/senior_project_update/blob/main/seniorProject_withoutStructure_Output_18_6/agents/query_classification_agent.py#L54-L170)
  - สรุปผล [result](https://github.com/ffahpatcha/senior_project_update/blob/main/withoutOutofDomain_samePrompt_25_6/README.md#%E0%B8%9C%E0%B8%A5%E0%B8%A5%E0%B8%B1%E0%B8%9E%E0%B8%98%E0%B9%8C)
