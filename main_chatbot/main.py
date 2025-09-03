import os
import time
import json
import uuid
import asyncio
import logging
from typing import List, Optional, Literal, Union, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator

from state_schema import AgentState
from my_agents.dental_guardrail_agent import run_dental_guardrail_check
from my_agents.hybrid_searcher import QDRANT_URL, QDRANT_API_KEY
from main_graph import graph

# -----------------------------------------------------------------------------
# Config & App
# -----------------------------------------------------------------------------
MODEL_ID = os.getenv("MODEL_ID", "custom-model")
GUARDRAIL_TIMEOUT_S = int(os.getenv("GUARDRAIL_TIMEOUT_S", "8"))
WORKFLOW_TIMEOUT_S = int(os.getenv("WORKFLOW_TIMEOUT_S", "60"))

app = FastAPI(title="OpenAI-compatible Chat API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://host.docker.internal:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn.error")

# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool", "function"] = "user"
    content: Union[str, List[dict], None] = ""

    @field_validator("content", mode="before")
    @classmethod
    def coerce_content_to_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, list):
            texts = [part.get("text", "") for part in v if isinstance(part, dict) and part.get("type") == "text"]
            return " ".join(texts)
        return str(v)
 
class ChatRequest(BaseModel):
    model: Optional[str] = Field(default=MODEL_ID)
    messages: List[ChatMessage]
    stream: Optional[bool] = False

class ChatChoice(BaseModel):
    index: int
    message: dict
    finish_reason: Optional[str] = "stop"

class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

class ModelCard(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str = "you"

class ModelList(BaseModel):
    object: Literal["list"] = "list"
    data: List[ModelCard]

class HybridInput(BaseModel):
    model_config = ConfigDict(strict=True)
    text: str
    category: Optional[Dict[str, str]] = None

    @model_validator(mode="before")
    def check_category_structure(cls, values):
        category = values.get("category")
        if category is not None:
            if "level_1" not in category or "level_2" not in category:
                raise ValueError("กรุณาระบุทั้ง `level_1` และ `level_2` ใน category")
        return values

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------
def latest_user_text(messages: List["ChatMessage"]) -> str:
    for m in reversed(messages):
        if m.role == "user":
            t = (m.content or "").strip()
            if t:
                return t
    return ""

def prior_user_context(messages: List["ChatMessage"], k: int = 2) -> list[str]:
    latest = latest_user_text(messages)
    buf, skip_latest = [], True
    for m in reversed(messages):
        if m.role != "user":
            continue
        t = (m.content or "").strip()
        if not t:
            continue
        if skip_latest and t == latest:
            skip_latest = False
            continue
        buf.append(t)
        if len(buf) >= k:
            break
    return list(reversed(buf))

async def run_guardrail(latest_user_text: str, req_id: str):
    try:
        return await asyncio.wait_for(
            run_dental_guardrail_check(latest_user_text),  # ใช้เฉพาะข้อความล่าสุด
            timeout=GUARDRAIL_TIMEOUT_S
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Guardrail timed out.")
    except Exception as e:
        logger.exception(f"[{req_id}] Guardrail error: {e}")
        raise HTTPException(status_code=500, detail=f"Guardrail error: {str(e)}")

async def run_workflow(latest_user_text: str, short_ctx: List[str], req_id: str) -> str:
    try:
        state = AgentState(
            user_query=latest_user_text,          # คงช่องเก่าเพื่อ compatibility
            user_query_latest=latest_user_text,   # ใช้จริงในกราฟ
            short_context=short_ctx,              # ส่งบริบทสั้น ๆ ให้โหนดถัดไปใช้
        )
    except Exception as e:
        logger.exception(f"[{req_id}] AgentState validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid AgentState: {e}")

    try:
        if hasattr(graph, "ainvoke") and callable(getattr(graph, "ainvoke")):
            result = await asyncio.wait_for(graph.ainvoke(state), timeout=WORKFLOW_TIMEOUT_S)
        else:
            result = await asyncio.wait_for(asyncio.to_thread(graph.invoke, state), timeout=WORKFLOW_TIMEOUT_S)

        if isinstance(result, dict):
            return result.get("response", "ไม่พบ response")
        response = getattr(result, "response", None)
        if response is None and hasattr(result, "dict"):
            response = result.dict().get("response")
        return response or "ไม่พบ response"

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Workflow timed out.")
    except RecursionError as e:
        logger.exception(f"[{req_id}] Workflow recursion: {e}")
        raise HTTPException(status_code=500, detail="Workflow recursion detected (graph loop).")
    except Exception as e:
        logger.exception(f"[{req_id}] Workflow error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow error: {e}")

def make_completion_response(content: str, req: ChatRequest) -> JSONResponse:
    response = ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=req.model or MODEL_ID,
        choices=[ChatChoice(index=0, message={"role": "assistant", "content": content})]
    )
    return JSONResponse(content=response.model_dump(), media_type="application/json; charset=utf-8")

def make_stream_response(content: str, model: str):
    async def stream():
        chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant", "content": content},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/v1")

@router.get("/healthz")
async def healthz():
    return {"status": "ok", "model": MODEL_ID, "time": int(time.time())}

@router.get("/models", response_model=ModelList)
async def list_models():
    return ModelList(data=[ModelCard(id=MODEL_ID, created=int(time.time()))])

@router.post("/chat/completions")
async def chat(req: ChatRequest):
    req_id = uuid.uuid4().hex[:8]
    logger.info(f"[{req_id}] /chat/completions called: stream={req.stream}")

    if not req.messages:
        raise HTTPException(status_code=400, detail="'messages' field is required.")

    # ดึงเฉพาะ “ผู้ใช้ล่าสุด” และ “บริบทสั้น ๆ”
    latest = latest_user_text(req.messages)
    short_ctx = prior_user_context(req.messages, k=2)

    # 1) Guardrail — เฉพาะ “ล่าสุด”
    gr = await run_guardrail(latest, req_id)
    triggered = bool(getattr(gr, "tripwire_triggered", False))
    logger.info(f"[{req_id}] guardrail.triggered={triggered}")
    if triggered:
        reason = (getattr(gr, "output_info", {}) or {}).get("reasoning", "ไม่ได้ระบุเหตุผล")
        return make_completion_response(
            "ขอโทษค่ะ ระบบนี้ตอบได้เฉพาะคำถามเกี่ยวกับการดูแลหลังถอนฟันหรือผ่าฟันคุดเท่านั้น\n\n"
            "ลองพิมพ์ใหม่เป็นคำถามเฉพาะเจาะจง เช่น:\n"
            "• “หลังผ่าฟันคุด 24 ชม.แรก ควรกิน/เลี่ยงอะไรบ้าง?”\n"
            "• “เพิ่งถอนฟันมา ใช้เกลือกลั้วปากได้เมื่อไหร่?”\n"
            "• “เลือดซึมไม่หยุดหลังถอนฟัน ควรทำอย่างไร?”\n\n"
            "หมายเหตุ: หากมีอาการฉุกเฉิน เช่น เลือดออกมากไม่หยุด ปวดรุนแรงผิดปกติ "
            "บวมลาม/มีไข้สูง/กลืนลำบาก หายใจลำบาก โปรดติดต่อโรงพยาบาลหรือทันตแพทย์ใกล้คุณทันที\n\n"
            f"(รายละเอียดจากระบบความปลอดภัย: {reason})", req
        )

    # 2) Workflow — ส่ง “ล่าสุด + บริบทสั้น ๆ” ให้กราฟ
    response_text = await run_workflow(latest, short_ctx, req_id)

    if req.stream:
        return make_stream_response(response_text, req.model or MODEL_ID)
    return make_completion_response(response_text, req)

app.include_router(router)

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
