from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from main_graph import graph
from state_schema import AgentState
from my_agents.dental_guardrail_function import run_dental_guardrail_check

from agents import Runner
import time

app = FastAPI()


@app.post("/v1/chat/completions")
async def chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])

    if not messages:
        return JSONResponse(
            status_code=400,
            content={"error": "messages field is required"}
        )

    # รวมข้อความทั้งหมดเป็น string
    conversation_history = ""
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "user":
            conversation_history += f"\n[User]: {content}"
        elif role == "assistant":
            conversation_history += f"\n[Assistant]: {content}"

    # เรียก Guardrail Pre-check
    try:
        
        guardrail_result = await run_dental_guardrail_check(conversation_history)


        # Debug Log
        print("guardrail_result:", guardrail_result)

        if guardrail_result is None:
            return JSONResponse(
                status_code=500,
                content={"error": "Guardrail returned None"}
            )

        if getattr(guardrail_result, "tripwire_triggered", False):
            return JSONResponse(
                content={
                    "id": "chatcmpl-xyz",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "custom-model",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": (
                                    "ขอโทษค่ะ ระบบนี้ตอบได้เฉพาะคำถามเกี่ยวกับการดูแลหลังถอนฟันหรือผ่าฟันคุดเท่านั้น\n\n"
                                    f"เหตุผล: {guardrail_result.output_info.get('reasoning', 'ไม่ได้ระบุเหตุผล')}"
                                )
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                },
                media_type="application/json; charset=utf-8"
            )

    except Exception as e:
        # ถ้าเกิด error ใน Guardrail
        return JSONResponse(
            status_code=500,
            content={"error": f"Guardrail error: {str(e)}"}
        )

    # ถ้าไม่ tripwire, เริ่ม Workflow ตามปกติ
    initial_state = AgentState(
        user_query=conversation_history
    )

    raw_state = await graph.ainvoke(initial_state)

    response_text = raw_state.get("response", "❌ ไม่พบ response")

    return JSONResponse(
        content={
            "id": "chatcmpl-xyz",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "custom-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        },
        media_type="application/json; charset=utf-8"
    )


@app.get("/v1/models")
async def list_models():
    return JSONResponse(
        content={
            "object": "list",
            "data": [
                {
                    "id": "custom-model",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "you"
                }
            ]
        }
    )
