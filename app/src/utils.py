import yaml
# from text_constants import *
from src.text_constants import LLM_URL
import json
from retry import retry
import requests
import re
from typing import Optional, Dict, Union
from src.text_constants import (GeneralValuesLLM, AppSettings,
                                Keys, LoggerMsg, GeneralUtilitsConsts)
from src.logger import log_function_call,LOGGER


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

@retry(tries=GeneralUtilitsConsts.RETRY_TRIES)
@log_function_call()
def generate_response(prompt_input: Optional[str],
                    model_params: Optional[Dict[str, Union[float, int]]] = None,
                    temp: float = GeneralValuesLLM.GEN_RESPONSE_TEMP,
                    max_tokens: int = GeneralValuesLLM.GEN_RESPONSE_MAX_TOKENS,
                    repetition_penalty: float = GeneralValuesLLM.GEN_RESPONSE_REPETITION_PENALTY,
                    frequency_penalty: float = GeneralValuesLLM.GEN_RESPONSE_FREQUENCY_PENALTY) -> Optional[str]:
    # answer = None
    try:

        if model_params is not None:
            temp = model_params.get('temperature', temp)
            max_tokens = model_params.get('max_new_tokens', max_tokens)
            repetition_penalty = model_params.get('repetition_penalty', repetition_penalty)
            frequency_penalty = model_params.get('frequency_penalty', frequency_penalty)
            
        data = {"inputs": prompt_input,
                "parameters": {
                    "top_k": GeneralValuesLLM.GEN_RESPONSE_TOP_K,
                    "top_n_tokens": GeneralValuesLLM.GEN_RESPONSE_TOP_N_TOKENS,
                    "top_p": GeneralValuesLLM.GEN_RESPONSE_TOP_P,
                    "temperature": temp,
                    "max_new_tokens": max_tokens,
                    "frequency_penalty": frequency_penalty,
                    "do_sample": True,
                    "repetition_penalty": repetition_penalty,
                }
                }
        output = requests.post(url=LLM_URL,
                               headers=GeneralUtilitsConsts.HEADERS,
                               json=data,
                               timeout=60)
        answer = json.loads(output.text)[Keys.GENERATED_TEXT]

        if not answer.strip():  # Проверяем, что строка не пустая
            raise ValueError(AppSettings.USER_ERROR_MSG.format(AppSettings.WIKI_TEMPLATE))
        return answer
    except Exception as error:
        LOGGER.error(LoggerMsg.ERROR, str(error), generate_response.__name__, exc_info=True)
        raise