from pydantic import BaseModel
from typing import Optional, Dict, List

class CategoryScore(BaseModel):
    subcategory: str
    confidence: float

class ClassificationResult(BaseModel):
    category_level_1: Optional[str] = None
    category_level_2: Optional[List[CategoryScore]] = None
    clarification_needed: bool = False
    out_of_domain: bool = False
    selected_categories: Optional[List[str]] = None
    selected_categories_by_threshold: Optional[List[str]] = None
    retrieval_context: Optional[Dict] = None
    routing_decision: Optional[Dict] = None

class EvaluationResult(BaseModel):
    score: float
    reason: Optional[str] = None

class AgentState(BaseModel):
    user_query: str
    classification_result: Optional[ClassificationResult] = None
    rewritten_query: Optional[str] = None
    retrieved_context: Optional[str] = None
    generated_answer: Optional[str] = None
    evaluation_result: Optional[EvaluationResult] = None
    # tool_call_required: Optional[bool] = False
    # tool_input: Optional[str] = None
    # tool_result: Optional[str] = None
    final_answer: Optional[str] = None
