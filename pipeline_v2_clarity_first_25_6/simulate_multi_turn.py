from state_schema import AgentState
from main_graph import graph
from utils.query_rewrite import auto_rewrite_query
import json

# 🔵 Round 1: user เริ่มถาม
query1 = "เมื่อไหร่ยาจะหมดฤทธิ์"
state1 = AgentState(user_query=query1)
result1 = graph.invoke(state1)
final1 = AgentState(**result1)

print("\n🔵 Round 1")
print("❓ User:", final1.user_query)
print("🤖 Bot:", final1.response)

# ✅ ตรวจว่า LLM ต้องการ clarification ไหม
if final1.classification_result.clarification_needed:
    # 🟡 Round 2: สมมุติว่า user ตอบกลับ
    reply2 = "ถอนฟันกรามล่างซ้าย"

    # ✅ ใช้ rule-based query rewriting
    full_query = auto_rewrite_query(
        previous_user_query=final1.user_query,
        clarification_prompt=final1.response,
        user_reply=reply2
    )

    state2 = AgentState(
        user_query=full_query,
        previous_turns=final1.previous_turns + [final1.user_query, final1.response, reply2]
    )
    result2 = graph.invoke(state2)
    final2 = AgentState(**result2)

    print("\n🟡 Round 2 (Rewritten)")
    print("❓ User:",reply2)
    print("✏️ Rewritten query:", full_query)
    print("🤖 Bot:", final2.response)

    if final2.classification_result.category_level_1:
        print("\n✅ Category Level 1:")
        for cat in final2.classification_result.category_level_1:
            print(f"- {cat.category} ({cat.confidence:.2f})")

    if final2.classification_result.category_level_2:
        print("\n✅ Subcategory:")
        for sub in final2.classification_result.category_level_2:
            print(f"- {sub.subcategory} ({sub.confidence:.2f})")

    # ✅ แสดง JSON สุดท้าย
    print("\n📦 Final Output JSON:")
    print(json.dumps(final2.model_dump(), indent=2, ensure_ascii=False))

else:
    print("\n✅ ไม่ต้องถามกลับ")
    print(json.dumps(final1.model_dump(), indent=2, ensure_ascii=False))
