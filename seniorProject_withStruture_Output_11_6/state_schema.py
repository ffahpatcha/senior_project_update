# 📁 state_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal,Dict

class CategoryScore(BaseModel):
    category: str = Field(..., description="ชื่อหมวดหมู่ใหญ่ เช่น อาการ/ภาวะแทรกซ้อน, การปฏิบัติตัวหลังหัตถการ")
    confidence: float = Field(..., ge=0.0, le=1.0)

# ใช้สำหรับ category_level_2
class SubcategoryScore(BaseModel):
    subcategory: str = Field(..., description="ชื่อหมวดย่อย เช่น 'อาหาร', 'แผล'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="ค่าความมั่นใจ 0.0-1.0")


#Schema หลักสุดท้ายที่ใช้เก็บผลลัพธ์รวมทุกขั้น
class ClassificationResult(BaseModel):
    category_level_1: Optional[List[CategoryScore]] = Field(None, description="หมวดหมู่หลักพร้อม confidence")
    category_level_2: Optional[List[SubcategoryScore]] = Field(None, description="หมวดย่อยพร้อม confidence")
    clarification_needed: Optional[bool] = None
    out_of_domain: Optional[bool] = None

    def is_terminal(self) -> bool:
        return self.out_of_domain is True or self.clarification_needed is True


# ตัวเก็บ state ของ agent ทั้งหมด
class AgentState(BaseModel):
    user_query: str
    classification_result: ClassificationResult = Field(default_factory=ClassificationResult)
    latency: Optional[Dict[str, float]] = None
    def should_terminate(self) -> bool:
        return self.classification_result.is_terminal()
    response: Optional[str] = None

#Schema แยกสำหรับแต่ละขั้นตอนของ LLM structured output
class OutOfDomainResult(BaseModel):
    out_of_domain: bool
    reason: Optional[str] = None

class ClarificationResult(BaseModel):
    clarification_needed: bool
    reason: Optional[str] = None  # เพิ่มเพื่อให้โมเดลอธิบายได้


class CategoryResult(BaseModel):
    category_level_1: List[CategoryScore]
    category_level_2: List[SubcategoryScore]
