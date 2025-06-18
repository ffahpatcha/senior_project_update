from langchain_community.llms import Together
from config.settings import TOGETHER_API_KEY, TOGETHER_MODEL

def get_together_llm(model_name: str, temperature: float = 0.3, max_tokens: int = 1024):
    return Together(
        model=TOGETHER_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        together_api_key=TOGETHER_API_KEY
    )
