# generate node (context-mode, uses short memory from state.short_context)
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

from state_schema import AgentState
from llm_utils import get_together_llm, count_tokens
from settings import TOGETHER_MODEL


def _latest_question(state: AgentState) -> str:
    """ดึงคำถามล่าสุดจาก state (ใช้เป็น input ให้ LLM)"""
    return getattr(state, "user_query_latest", None) or state.user_query or ""


def _build_chat_memory(
    state: AgentState,
    max_items: int = 6,
    token_budget: int = 800,
) -> str:
    """
    สร้าง memory สั้น ๆ จาก state.short_context:
    - เก็บเทิร์นผู้ใช้ล่าสุด ๆ (1–2 รายการตามที่ upstream ใส่มา)
    - ตัดข้อความว่าง/ซ้ำ/ที่เป็นซับสตริงของคำถามล่าสุด เพื่อกัน noise
    - จำกัดโทเคนไม่ให้กิน context หลัก
    """
    latest = (_latest_question(state) or "").strip()
    raw = getattr(state, "short_context", None)

    items: List[str] = []
    if isinstance(raw, list):
        seen = set()
        for s in raw[-max_items:]:
            t = str(s or "").strip()
            if not t:
                continue
            if t in seen:
                continue
            if latest and (t == latest or t in latest):
                continue
            items.append(t)
            seen.add(t)

    memo_so_far = ""
    for it in items:
        prospective = memo_so_far + ("\n• " if memo_so_far else "• ") + it
        try:
            if count_tokens(prospective) > token_budget:
                break
        except Exception:
            # ถ้า tokenizer ล้ม ให้ใช้รายการที่มีอยู่
            break
        memo_so_far = prospective
    return memo_so_far


def _collect_docs_from_hits(
    state: AgentState,
    max_chunks: int = 8,
    token_budget: int = 3200,
) -> Tuple[List[Document], List[str]]:
    """
    รวม hits ทุกหมวด → เรียงตาม score → ตัดตามงบโทเคน
    คืนค่าเป็นรายการ Document สำหรับส่งเข้า chain และรายการ chunk_id ที่ใช้ (อ้างอิง)
    """
    retrieval = getattr(state, "retrieval_result", None)
    hits_by_category = getattr(retrieval, "hits_by_category", {}) if retrieval else {}

    entries = []
    for cat, hits in hits_by_category.items():
        for h in (hits or []):
            entries.append((cat, h))

    # เรียงจากคะแนนมากไปน้อย
    entries.sort(key=lambda x: float(getattr(x[1], "score", 0.0) or 0.0), reverse=True)

    docs: List[Document] = []
    used_chunk_ids: List[str] = []
    used_ids_set: set[str] = set()
    context_so_far = ""

    for cat, hit in entries:
        chunk_id = getattr(hit, "chunk_id", None)
        if not chunk_id or chunk_id in used_ids_set:
            continue

        snippet = " ".join(
            s.strip() for s in (getattr(hit, "snippets", []) or []) if s and s.strip()
        )
        if not snippet:
            continue

        chunk_text = f"({cat}) {snippet}".strip()
        prospective = f"{context_so_far}\n\n{chunk_text}" if context_so_far else chunk_text

        try:
            if count_tokens(prospective) > token_budget:
                break
        except Exception:
            # ถ้า tokenizer ล้ม ก็ถือว่าโอเค ใช้ตามลำดับไป
            pass

        docs.append(
            Document(
                page_content=chunk_text,
                metadata={
                    "chunk_id": chunk_id,
                    "score": float(getattr(hit, "score", 0.0) or 0.0),
                    "category": cat,
                },
            )
        )
        used_chunk_ids.append(chunk_id)
        used_ids_set.add(chunk_id)
        context_so_far = prospective

        if len(used_chunk_ids) >= max_chunks:
            break

    return docs, used_chunk_ids


def generate_node(state: AgentState) -> AgentState:
    """
    ทำงานต่อจาก hybrid_search_node:
      - ต้องมี state.retrieval_result.hits_by_category แล้ว
      - สร้าง chat_memory จาก state.short_context
      - ยัด context + memory ลง system prompt พร้อม persona/guardrails
      - เรียก LLM สร้างคำตอบภาษาไทย
    """
    question = _latest_question(state).strip()
    if not getattr(state, "retrieval_result", None) or not state.retrieval_result.hits_by_category:
        state.response = "ตอนนี้ยังไม่มีข้อมูลอ้างอิงจากการค้นหาเพื่อสรุปคำตอบครับ/ค่ะ"
        return state

    # รวบเอกสารเป็น context
    docs, used_chunk_ids = _collect_docs_from_hits(state, max_chunks=8, token_budget=3200)
    if not docs:
        state.response = "มีผลการค้นหาบางส่วน แต่ยังไม่พบข้อความที่นำมาสรุปได้ชัดเจนครับ/ค่ะ"
        return state

    # memory/chat_history แบบสั้นจาก short_context
    chat_history = _build_chat_memory(state, max_items=6, token_budget=800)

    # Persona + guardrails + memory + context
    prompt = ChatPromptTemplate.from_messages(
[
    (
        "system",
        "บทบาท/Persona: ผู้ช่วยดูแลหลังทำหัตถการทางทันตกรรมที่สุภาพ พูดแบบไทย\n"
        "ขอบเขตงาน: ให้คำแนะนำทั่วไปหลังหัตถการ (เช่น ถอนฟัน/ผ่าฟันคุด/อุดฟัน/ขูดหินปูน/ผ่าตัดทางช่องปาก) "
        "โดยอ้างอิงเฉพาะ ‘บริบทจากเอกสาร’ ที่ให้มาเท่านั้น ห้ามเดาข้อมูลที่ไม่มีในบริบท\n"
        "นอกเหนือขอบเขตหรือไม่มีข้อมูลเพียงพอ: บอกว่าไม่แน่ใจ/ไม่มีข้อมูล และระบุข้อมูลที่ต้องการเพิ่ม "
        "(เช่น ประเภทหัตถการ, เวลาหลังทำ, อาการปัจจุบัน, ยาที่ใช้/แพ้ยา, โรคประจำตัว/ตั้งครรภ์/ยาละลายลิ่มเลือด) แล้วเสนอแนวทางที่ปลอดภัย\n"
        "ความปลอดภัย: หลีกเลี่ยงการวินิจฉัยหรือสั่งยาเอง หากในบริบทมีคำแนะนำเรื่องยา ให้ระบุชื่อยา, ขนาด, ความถี่, หน่วย และช่วงเวลาอย่างชัดเจน "
        "ถ้าไม่มีในบริบท ให้ระบุว่า ‘บริบทไม่ได้ระบุข้อมูลยา’ และแนะนำปรึกษาทันตแพทย์/เภสัชกร\n"
        "สัญญาณอันตราย/การส่งต่อ: หากในบริบทระบุอาการที่ต้องพบแพทย์ ให้สรุปชัดเจนและแนะนำไปพบทันตแพทย์หรือห้องฉุกเฉินที่ใกล้ที่สุดตามความเหมาะสม\n"
        "สไตล์คำตอบ: กระชับ ชัด ขั้นเป็นข้อ ใช้ภาษาที่ให้กำลังใจ ไม่ทำให้ตระหนกเกินจำเป็น "
        "อธิบายเป็นช่วงเวลา (เช่น 24 ชม.แรก / วันที่ 2–3 / 1 สัปดาห์) และใช้ตัวเลข+หน่วยที่ชัดเจน\n"
        "ข้อจำกัด: หากเนื้อหาในบริบทขัดแย้งกัน ให้เลือกใช้คำแนะนำที่ ‘คงที่/ปลอดภัยกว่า’ และระบุว่าเนื้อหามีความคลาดเคลื่อน\n"
        "รูปแบบผลลัพธ์ (ปรับใช้เท่าที่เหมาะ):\n"
        "- ประโยคเปิดสั้น 1-2 บรรทัดที่สรุปใจความ (ห้ามใช้คำว่า ‘สรุป’, ‘สรุปสั้น ๆ’, ‘โดยสรุป’ หรือขึ้นหัวข้อใด ๆ)\n"
        "- ✅ควรทำ\n"
        "- ⛔️ควรเลี่ยง\n"
        "- 🪥วิธีดูแล/ขั้นตอน\n"
        "- ⚠️สัญญาณอันตรายที่ควรพบแพทย์ (ถ้ามีในบริบท)\n"
        "ปิดท้ายด้วยคำถามสั้น ๆ เพื่อเช็คต่อ เช่น “มีอาการอะไรเพิ่มเติมอยากเล่าไหมคะ?”\n"
        "หมายเหตุ: คำแนะนำเป็นข้อมูลทั่วไป ไม่แทนการตรวจรักษาจากบุคลากรทางการแพทย์\n\n"
        "ประวัติสนทนาล่าสุด (ย่อ):\n{chat_history}\n\n"
        "บริบทจากเอกสาร (ใช้ตอบเท่านั้น):\n{context}"
    ),
    ("human", "คำถาม: {input}"),
]
)



    text: str | None = None
    try:
        llm = get_together_llm(model=TOGETHER_MODEL, temperature=0.1)
        qa_chain = create_stuff_documents_chain(llm, prompt)
        out = qa_chain.invoke({"input": question, "context": docs, "chat_history": chat_history})
        if isinstance(out, str):
            text = out
        elif isinstance(out, dict):
            text = out.get("output_text") or out.get("text") or out.get("answer") or str(out)
        else:
            text = str(out)
    except Exception as e:
        state.errors.append(f"generate_llm_error: {e}")
        text = None

    if not text:
        bullets = [d.page_content for d in docs[:6] if d.page_content.strip()]
        text = "สรุปจากข้อมูลที่ค้นเจอ:\n" + "\n".join(f"- {b}" for b in bullets)

    refs = ", ".join(used_chunk_ids[:5])
    if refs:
        text = f"{text}\n\n(อ้างอิง: {refs})"

    state.response = text
    return state
