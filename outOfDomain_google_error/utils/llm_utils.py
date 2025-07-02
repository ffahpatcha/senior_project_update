# 📁 utils/llm_utils.py
from langchain_together import ChatTogether
from pydantic import BaseModel
from config.settings import TOGETHER_API_KEY, TOGETHER_MODEL  
from state_schema import ClassificationResult
import tiktoken

def get_together_llm(model: str, temperature: float = 0.3, max_tokens: int = 1024, **kwargs):
    """
    Initializes and returns a Together LLM instance, optionally configured for structured output
    """
    llm = ChatTogether(
        model=TOGETHER_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=TOGETHER_API_KEY 
    )

    # หากมี structured_output_schema และเป็น Pydantic schema
    if "structured_output_schema" in kwargs:
        schema = kwargs["structured_output_schema"]
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                return llm.with_structured_output(schema)
            except (AttributeError, NotImplementedError):
                print("⚠️  This LLM does not support structured output via .with_structured_output().")
    
    return llm

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))