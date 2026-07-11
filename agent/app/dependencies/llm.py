from langchain_openai import ChatOpenAI
from app.core.config import settings

_llm = None

def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=settings.OPENAI_MODEL,
            temperature=0.3,
            timeout=60,
        )
    return _llm