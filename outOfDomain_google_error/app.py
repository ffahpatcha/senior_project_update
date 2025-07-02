import streamlit as st
from main_graph import graph
from state_schema import AgentState

st.title("Dental Assistant Bot")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.text_input("พิมพ์คำถาม", key="input")

if st.button("ส่ง"):
    state = AgentState(user_query=user_input)
    raw_state = graph.invoke(state)
    response = raw_state.get("response") or "✅ Done, ไม่มี response โดยตรง"
    st.session_state.history.append({"query": user_input, "response": response})

for h in reversed(st.session_state.history):
    st.write(f"**คุณ:** {h['query']}")
    st.write(f"**บอท:** {h['response']}")
