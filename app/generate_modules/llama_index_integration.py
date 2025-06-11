from llama_index.core import ListIndex, Document
from llama_index.core import Settings
import requests
from dotenv import load_dotenv
import os
from retry import retry
from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
)
from src.text_constants import *
from src.numerical_constants import *
from src.logger import LOGGER

load_dotenv()

class LocalLLM(CustomLLM):
    host: str = os.getenv("LLM_URL")
    headers: dict = HEADERS

    @retry(tries=RETRY_TRIES)
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        """Генерирует ответ на основе промпта."""
        data = {
            "inputs": prompt,
            "parameters": {
                "top_k": kwargs.get("top_k", 50),
                "top_p": kwargs.get("top_p", 0.95),
                PARAMETR_TEMPERATURE: kwargs.get(PARAMETR_TEMPERATURE, \
                                                 GEN_RESPONSE_TEMP),
                PARAMETR_MAX_NEW_TOKENS: kwargs.get(PARAMETR_MAX_NEW_TOKENS, \
                                                    GEN_RESPONSE_MAX_TOKENS),
                PARAMETR_FREQUENCY_PENALTY: kwargs.get(PARAMETR_FREQUENCY_PENALTY, \
                                                       GEN_RESPONSE_FREQUENCY_PENALTY),
                "do_sample": kwargs.get("do_sample", True),
                PARAMETR_REPETITION_PENALTY: kwargs.get(PARAMETR_REPETITION_PENALTY, \
                                                        GEN_RESPONSE_FREQUENCY_PENALTY),
            }
        }

        response = requests.post(
            url=self.host,
            headers=self.headers,
            json=data,
            timeout=60
        )
        answer = response.json()[KEY_GENERATED_TEXT]
        # answer = json.loads(response.text[KEY_GENERATED_TEXT])
        # print(answer)
        
        if response.status_code == 200:
            # if answer in ERROR_RESPONSE_LLM_MSG:
            #     return ERROR_RESPONSE_LLM_MSG
            # else:
            return answer
        else:
            raise Exception(f"{ERROR_RESPONSE_LLM} {response}")

    def stream_complete(self, prompt: str, **kwargs):
        """Потоковая генерация не поддерживается."""
        raise NotImplementedError(ERROR_NOTIMPLEMENTEDERROR)

    @property
    def metadata(self) -> LLMMetadata:
        """Возвращает метаданные о модели."""
        return LLMMetadata(model_name=MODEL_LOCAL_NAME)

def create_service_context(llm):
    """Создаёт контекст для работы с LLamaIndex."""
    Settings.llm = llm  # Создание настроек с использованием llm
    return Settings

def generate_test_cases_with_memory(prompt: str, count: int, existing_cases: list) -> list:
    """
    Генерирует тест-кейсы с учётом уже сгенерированных.
    
    :param prompt: Описание задачи
    :param count: Количество кейсов для генерации
    :param existing_cases: Список уже сгенерированных тестов
    :return: Список новых уникальных тестов
    """
    LOGGER.info(LOGGER_INFO_START, generate_test_cases_with_memory.__name__)
    
    # Формируем полный промпт
    context = "\n\n".join(existing_cases)  # Объединяем существующие кейсы в строку
    full_prompt = f"{prompt}{PROMPT_EXIST_CASES}{context}"

    documents = [Document(text=case) for case in existing_cases]
    list_index = ListIndex(documents)

    llm = LocalLLM()
    response_text = llm.complete(full_prompt).strip()
    cases = [case.strip() for case in response_text.split("\n\n") if case.strip()]

    # Фильтрация уникальных
    unique_cases = [case for case in cases if case not in existing_cases]

    # === Обновляем индекс новыми кейсами ===
    for new_case in unique_cases[:count]:
        list_index.insert(Document(text=new_case))

    LOGGER.info(LOGGER_INFO_END, generate_test_cases_with_memory.__name__)

    return unique_cases[:count]