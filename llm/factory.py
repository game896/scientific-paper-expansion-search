from config import Settings
from llm.fake import FakeLLM
from llm.gemini import GeminiLLM
from llm.interface import LLM


def create_llm(settings: Settings) -> LLM:
    if settings.llm_provider == "gemini":
        return GeminiLLM(settings.gemini_api_key, settings.gemini_llm_model)
    return FakeLLM()
