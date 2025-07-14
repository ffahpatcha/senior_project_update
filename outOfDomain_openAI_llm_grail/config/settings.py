from dotenv import load_dotenv
import os

load_dotenv()

TOGETHER_MODEL = os.getenv("TOGETHER_MODEL")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
