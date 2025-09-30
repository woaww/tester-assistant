import yaml
from src.text_constants import LLM_URL
import json
import os
import pandas as pd
import re
from src.text_constants import (GeneralValuesLLM, AppSettings,
                                Keys, GeneralUtilitsConsts)
from src.logger import log_function_call
import httpx
import asyncio
import json
from tenacity import retry, stop_after_attempt, wait_exponential


def ensure_stats_file(file_path: str) -> None:
    """
    Проверяет наличие файла по указанному пути.
    Если файл или директория отсутствуют, создаёт их.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        pd.DataFrame(columns=['url','path','method','response','rating']).to_csv(file_path, index=False)

@log_function_call()
def load_prompts(file_path="prompts.yaml"):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
@log_function_call()
def split_wiki_jira_tests_by_separator(text):
    full_text = "\n".join(text)
    # Разбиваем текст по "---\n\n"
    blocks = full_text.strip().split("---\n\n")
    b_blocks = [block.strip() for block in blocks if block.strip()]
    
    # Удаляем пустые блоки
    # return [block.strip() for block in blocks if block.strip()]
    formatted_text = "\n\n".join(b_blocks)
    
    return formatted_text

@log_function_call()
def split_api_test_cases(data):
    # full_text = "\n".join(data)
    test_cases = []
    current_case = ""
    
    for line in data:
        # Проверяем, начинается ли строка с номера (например: "1. ", "2. ", ...)
        if re.match(r'^\d+\.\s', line.strip()):
            if current_case:
                test_cases.append(current_case.strip())
            current_case = line
        else:
            current_case += "\n" + line
    
    if current_case:
        test_cases.append(current_case.strip())

    formatted_text = "\n\n".join(test_cases)
    
    return formatted_text

@log_function_call()
# retry с экспоненциальным бэкофом
@retry(stop=stop_after_attempt(GeneralUtilitsConsts.RETRY_TRIES), 
       wait=wait_exponential(multiplier=1, min=2, max=30))
async def generate_response_async(prompt_input: str,
                                  model_params: dict = None,
                                  temp: float = GeneralValuesLLM.GEN_RESPONSE_TEMP,
                                  max_tokens: int = GeneralValuesLLM.GEN_RESPONSE_MAX_TOKENS,
                                  repetition_penalty: float = GeneralValuesLLM.GEN_RESPONSE_REPETITION_PENALTY,
                                  frequency_penalty: float = GeneralValuesLLM.GEN_RESPONSE_FREQUENCY_PENALTY) -> str:
    """
    Асинхронный запрос к LLM с ретраями
    """
    if model_params:
        temp = model_params.get('temperature', temp)
        max_tokens = model_params.get('max_new_tokens', max_tokens)
        repetition_penalty = model_params.get('repetition_penalty', repetition_penalty)
        frequency_penalty = model_params.get('frequency_penalty', frequency_penalty)

    data = {
        "inputs": prompt_input,
        "parameters": {
            "top_k": GeneralValuesLLM.GEN_RESPONSE_TOP_K,
            "top_n_tokens": GeneralValuesLLM.GEN_RESPONSE_TOP_N_TOKENS,
            "top_p": GeneralValuesLLM.GEN_RESPONSE_TOP_P,
            "temperature": temp,
            "max_new_tokens": max_tokens,
            "frequency_penalty": frequency_penalty,
            "do_sample": False,
            "repetition_penalty": repetition_penalty,
        }
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            url=LLM_URL,
            headers=GeneralUtilitsConsts.HEADERS,
            json=data
        )
        response.raise_for_status()
        answer = response.json().get(Keys.GENERATED_TEXT)

        if not answer or not answer.strip():
            raise ValueError(AppSettings.USER_ERROR_MSG.format(AppSettings.WIKI_TEMPLATE))

        return answer

@log_function_call()
def sync_generate_response(prompt_input: str, model_params: dict = None) -> str:
    """
    Синхронная обёртка для асинхронной функции generate_response_async.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            generate_response_async(prompt_input, model_params)
        )
    finally:
        loop.close()
