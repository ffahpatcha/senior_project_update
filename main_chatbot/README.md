# main_chatbot Date 3/9
ปรับ generate node 

## Folders หลัก
- qdrant prepare [qdrant](https://github.com/ffahpatcha/senior_project_update/tree/main/main_chatbot/qdrant)
- agents
  - out of domain checker node  [dental_guardrail_agent.py](https://github.com/ffahpatcha/senior_project_update/blob/main/main_chatbot/my_agents/dental_guardrail_agent.py) : ใช้ llm  gpt-4o จาก openAI API
  - query clarify node [query_classification_agent.py (บรรทัด 25–174)](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_google_error/agents/query_classification_agent.py#L25-L174) : ใช้ llm meta-llama/Llama-3.3-70B-Instruct-Turbo จาก together.ai 
  - query classification node [query_classification_agent.py (บรรทัด 177-325)](https://github.com/ffahpatcha/senior_project_update/blob/main/outOfDomain_google_error/agents/query_classification_agent.py#L177-L325) : ใช้ llm meta-llama/Llama-3.3-70B-Instruct-Turbo จาก together.ai 
  - hybrid search node [hybrid_searcher.py](https://github.com/ffahpatcha/senior_project_update/blob/main/main_chatbot/my_agents/hybrid_searcher.py)
    <img width="1823" height="1020" alt="image" src="https://github.com/user-attachments/assets/be845fca-905e-43e1-818a-399f338f4eb1" />
    <img width="1697" height="981" alt="image" src="https://github.com/user-attachments/assets/d6086fe4-7af4-43a6-a300-103c50c012f2" />
  - generate node [generate_agent.py](https://github.com/ffahpatcha/senior_project_update/blob/main/main_chatbot/my_agents/generate_agent.py)
- main langgraph [main_graph.py](https://github.com/ffahpatcha/senior_project_update/blob/main/main_chatbot/main_graph.py)
  - เชื่อม pipeline |  query clarify node -> query classification node -> hybrid search node -> generate node
- main router [main.py](https://github.com/ffahpatcha/senior_project_update/blob/main/main_chatbot/main.py)
  - out of domain checker -> langgraph 
  - เชื่อม backend กับ frontend(openwebui) เชื่อมผ่าน fastAPI 
  
## ภาพรวมคำตอบ chatbot
- กรณี out of domain
  
  <img width="1039" height="415" alt="image" src="https://github.com/user-attachments/assets/0910587e-0585-4247-ab9c-3f99c4c72da3" />

- กรณี clarify needed
  
  <img width="1153" height="438" alt="image" src="https://github.com/user-attachments/assets/7f5c615b-c66b-431b-a6b4-dcd26d36aea8" />

- กรณี ผ่านclassification node
  - prompt1
    
    <img width="954" height="353" alt="image" src="https://github.com/user-attachments/assets/fa384e2a-5522-4ac5-a693-1eb97d61fa76" />

    - chunk ที่ retrieve มา เป็น context ที่สามารถตอบคำถามได้
      
      <img width="1134" height="604" alt="image" src="https://github.com/user-attachments/assets/b9a47a71-4288-4368-b1cb-61cd2c71310e" />

    - chunk ที่ retrieve มา context ยังไม่เพียงพอสำหรับการตอบคำตอบ
      
      <img width="1309" height="326" alt="image" src="https://github.com/user-attachments/assets/275c9906-d1ce-4422-aa12-402790dc03c4" />

  - prompt2
    
    <img width="1707" height="887" alt="image" src="https://github.com/user-attachments/assets/d54a3da3-2534-47c0-b611-2db214013307" />


    - chunk ที่ retrieve มา เป็น context ที่สามารถตอบคำถามได้
      
      <img width="916" height="338" alt="image" src="https://github.com/user-attachments/assets/fd9a69f4-fcad-4906-ac1d-cb1a24f19663" />
      <img width="2055" height="772" alt="image" src="https://github.com/user-attachments/assets/48a17f47-f1c2-4cfb-832f-466cbf8ff1c9" />

      
## ปัญหา/แก้เพิ่ม
- input ที่เข้า node out of domain,clarify,classify,hybrid search เป็น latest query ซึ่งยังไม่แน่ใจว่าเหมาะสมกับ chatbot แล้วหรือยัง
- input ที่เข้า node generate node มี query (latest question) กับ memory(message ส่วนของ user 2 อันท้าย)
- กรณีที่ clarify needed,out of domain = true  ถ้าระบบส่งคำตอบข้างต้น(รูปภาพรวม คำตอบ chatbot) เหมาะสมแล้วหรือไม่ หรือควรที่จะมีการปรับให้หน้า ui ขึ้นเป็นตัวเลือก question ขึ้นให้ user กด
  








