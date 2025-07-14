from state_schema import QueryState

def retrieve_context(state: QueryState) -> QueryState:
    cat2 = state.classification_result.category_level_2 or []
    category = cat2[0]["subcategory"] if cat2 else "ไม่ทราบหมวด"
    state.retrieved_context = f"[Mock context สำหรับ: {category}]"
    return state
