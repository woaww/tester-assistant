import asyncio
import yaml
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.exceptions import LLMInvalidResponseError
from src.llm_provider import create_async_openai_client, get_llm_chat_model
from src.logger import log_function_call
from src.text_constants import GeneralUtilitsConsts, GeneralValuesLLM


@log_function_call()
def load_prompts(file_path="prompts.yaml"):
    """
    Загружает prompts.yaml.

    Важно: streamlit может запускать процесс из разного текущего каталога,
    поэтому сначала пробуем путь как есть, затем ищем prompts.yaml относительно app/.
    """
    candidate = Path(file_path)
    if candidate.is_file():
        with candidate.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # utils.py находится в app/src/, значит app/ = parent.parent
    app_dir = Path(__file__).resolve().parent.parent
    candidate2 = app_dir / file_path
    if candidate2.is_file():
        with candidate2.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    raise FileNotFoundError(f"Не найден prompts.yaml по путям: {candidate} или {candidate2}")


@retry(
    wait=wait_exponential(multiplier=1, max=30),
    stop=stop_after_attempt(GeneralUtilitsConsts.RETRY_TRIES),
    retry=retry_if_exception_type(LLMInvalidResponseError),
    reraise=True,
)
async def generate_response_async(
    prompt_input: str,
    model_params: dict = None,
    temp: float = GeneralValuesLLM.GEN_RESPONSE_TEMP,
    max_tokens: int = GeneralValuesLLM.GEN_RESPONSE_MAX_TOKENS,
    repetition_penalty: float = GeneralValuesLLM.GEN_RESPONSE_REPETITION_PENALTY,
    frequency_penalty: float = GeneralValuesLLM.GEN_RESPONSE_FREQUENCY_PENALTY,
) -> str:
    """
    Асинхронный запрос к LLM через OpenAI-совместимый API с ретраями.
    """

    # Обновление параметров из model_params, если переданы
    temp = model_params.get("temperature", temp) if model_params else temp
    max_tokens = model_params.get("max_new_tokens", max_tokens) if model_params else max_tokens
    repetition_penalty = model_params.get("repetition_penalty", repetition_penalty) if model_params else repetition_penalty
    frequency_penalty = model_params.get("frequency_penalty", frequency_penalty) if model_params else frequency_penalty

    client = create_async_openai_client()
    response = await client.chat.completions.create(
        model=get_llm_chat_model(),
        messages=[{"role": "user", "content": prompt_input}],
        temperature=temp,
        max_tokens=max_tokens,
        top_p=GeneralValuesLLM.GEN_RESPONSE_TOP_P,
        frequency_penalty=frequency_penalty,
        presence_penalty=repetition_penalty - 1.0,
        extra_body={
            "top_k": GeneralValuesLLM.GEN_RESPONSE_TOP_K,
        },
        stream=False,
    )
    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        raise ValueError("Пустой ответ LLM")
    return answer

@log_function_call()
def sync_generate_response(prompt_input: str, model_params: dict = None) -> str:
    """
    Синхронная обёртка для асинхронной функции generate_response_async.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(generate_response_async(prompt_input, model_params))
    finally:
        loop.close()
