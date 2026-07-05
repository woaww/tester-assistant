import os
import openai
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value and value.strip() else default


def get_llm_base_url() -> str:
    return _env("LLM_BASE_URL", "http://127.0.0.1:1234/v1")


def get_llm_api_key() -> str:
    return _env("LLM_API_KEY", "local-free")


def get_llm_chat_model() -> str:
    return _env("LLM_CHAT_MODEL", "qwen2.5-7b-instruct")


def get_llm_tools_model() -> str:
    return _env("LLM_TOOLS_MODEL", get_llm_chat_model())


def get_browser_llm_model() -> str:
    return _env("BROWSER_LLM_MODEL", get_llm_chat_model())


def get_llm_timeout_s() -> float:
    raw = os.getenv("LLM_TIMEOUT_S", "").strip()
    if not raw:
        return 60.0
    try:
        return float(raw)
    except Exception:
        return 60.0


def get_llm_max_retries() -> int:
    raw = os.getenv("LLM_MAX_RETRIES", "").strip()
    if not raw:
        return 3
    try:
        return max(1, int(raw))
    except Exception:
        return 3


def create_async_openai_client() -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(
        api_key=get_llm_api_key(),
        base_url=get_llm_base_url(),
    )

