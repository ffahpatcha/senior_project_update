from state_schema import QueryState

def generate_answer(state: QueryState) -> QueryState:
    query = state.rewritten_query or state.user_query
    context = state.retrieved_context
    state.generated_answer = f"จากคำถาม '{query}' คำตอบคือ... (อิงจาก: {context})"
    return state
