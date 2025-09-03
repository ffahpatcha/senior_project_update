# state_schema.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict

# ---------- Clarify / OOD ----------
class OutOfDomainResult(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    out_of_domain: bool
    reason: Optional[str] = None

class ClarificationResult(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    clarification_needed: bool = Field(..., description="ต้องการถามเพิ่มหรือไม่")
    clarification_reason: Optional[str] = Field(default=None, description="เหตุผลที่ต้องการถามเพิ่ม (สั้น ๆ)")

# ---------- Classification ----------
class CategoryAssignment(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    level_1: str = Field(..., description="หมวดใหญ่ (ไทย) เช่น 'การปฏิบัติตัวหลังทำหัตถการ'")
    level_2: str = Field(..., description="หมวดย่อย (EN) เช่น 'oral hygiene'")
    score: float = Field(..., ge=0.0, le=1.0)
    source: Optional[str] = Field(None, description="ที่มา เช่น clf_v2, rules_v1")

    def cat_key(self) -> str:
        return f"{self.level_1}|{self.level_2}"

class ClassificationResult(BaseModel):
    # เปิด validate_assignment ได้ แต่ห้าม assign ฟิลด์ภายใน model_validator (จะเกิด recursion)
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    categories: List[CategoryAssignment] = Field(default_factory=list)

    clarification_needed: Optional[bool] = None
    clarification_reason: Optional[str] = None
    out_of_domain: Optional[bool] = None
    out_of_domain_reason: Optional[str] = None

    threshold: float = 0
    schema_version: str = "2.1"

    def is_terminal(self) -> bool:
        return bool(self.out_of_domain) or bool(self.clarification_needed)

    def top1(self) -> Optional[CategoryAssignment]:
        return max(self.categories, key=lambda x: x.score) if self.categories else None

    def groups_by_l1(self) -> Dict[str, List[CategoryAssignment]]:
        out: Dict[str, List[CategoryAssignment]] = {}
        for c in self.categories:
            out.setdefault(c.level_1, []).append(c)
        for k in out:
            out[k].sort(key=lambda x: x.score, reverse=True)
        return out

    @field_validator('categories', mode='after')
    @classmethod
    def _normalize_dedupe_threshold(cls, v: List[CategoryAssignment]) -> List[CategoryAssignment]:
        # ใช้ field_validator เพื่อหลีกเลี่ยงการ assign self.categories ภายใน model_validator
        def _norm(s: str) -> str:
            return " ".join((s or "").strip().split())

        # ใช้ threshold ดีฟอลต์ของคลาส (ถ้าต้องการ dynamic ตามอินสแตนซ์ อาจย้าย logic ไปก่อนหน้า)
        threshold = 0
        best: Dict[str, CategoryAssignment] = {}

        for c in v or []:
            # แก้ค่าที่ตัว c ได้ (validate_assignment ของ CategoryAssignment จะดูแลเอง)
            c.level_1 = _norm(c.level_1)
            c.level_2 = _norm(c.level_2)
            if c.score < threshold:
                continue
            k = c.cat_key()
            if (k not in best) or (c.score > best[k].score):
                best[k] = c

        return sorted(best.values(), key=lambda x: x.score, reverse=True)

# ---------- Retrieval ----------
class RetrievalHit(BaseModel):
    # เปิดให้ populate ได้ทั้งตามชื่อฟิลด์จริง (chunk_id) และ alias (doc_id)
    model_config = ConfigDict(extra='forbid', validate_assignment=True, populate_by_name=True)

    # ใช้ chunk_id เป็นฟิลด์หลัก และตั้ง alias='doc_id' เพื่ออ่านค่าเก่าได้อัตโนมัติ
    chunk_id: str = Field(alias='doc_id')
    score: float
    snippets: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # ใช้ Any (ตัวใหญ่)

class RetrievalResult(BaseModel):
    hits_by_category: Dict[str, List[RetrievalHit]] = Field(default_factory=dict)

# ---------- Agent state ----------
class AgentState(BaseModel):
    user_query: str  = ""
    user_query_latest: str = ""           # ข้อความผู้ใช้ล่าสุด (ใช้กับ guardrail / clarity / classify)
    short_context: List[str] = []         # บริบทสั้น ๆ (user turns ย้อนหลัง 1–2 รายการ) สำหรับโหนดถัด ๆ ไป

    classification_result: ClassificationResult = Field(default_factory=ClassificationResult)
    retrieval_result: RetrievalResult = Field(default_factory=RetrievalResult)


    # debug/ความผิดพลาดระหว่างทาง
    errors: List[str] = Field(default_factory=list)

    response: Optional[str] = None
    previous_turns: List[str] = Field(default_factory=list)
    terminated: bool = False
    
    def should_terminate(self) -> bool:
        return self.classification_result.is_terminal()
