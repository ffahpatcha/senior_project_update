from main_graph import app
from state_schema import QueryState

if __name__ == "__main__":
    query = input("💬 User query: ")
    state = QueryState(user_query=query)
    result = app.invoke(state)
    print("\n✅ Final Answer:")
    print(result.generated_answer)