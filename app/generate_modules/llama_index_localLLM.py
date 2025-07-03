# from typing import List, Optional, Union, Dict
# # from llama_index.core import ListIndex, Document
# # from llama_index.core import Settings
# import requests
# from retry import retry
# from llama_index.core.llms import (
#     CustomLLM,
#     CompletionResponse,
#     CompletionResponseGen,
#     LLMMetadata,
# )
# from src.text_constants import *
# from src.text_constants import LLM_URL
# from src.text_constants import (GeneralUtilitsConsts, GeneralValuesLLM, 
#                                 Keys, LoggerMsg)
# from src.numerical_constants import *
# from src.logger import LOGGER
# from src.models import *

# class LocalLLM(CustomLLM):

#     host: str = LLM_URL
#     headers: dict = GeneralUtilitsConsts.HEADERS
        
#     @retry(tries=GeneralUtilitsConsts.RETRY_TRIES)
#     def complete(self,
#                 prompt_input: Optional[str],
#                 model_params: Optional[Dict[str, Union[float, int]]] = None) -> Optional[str]:
#         LOGGER.info(LoggerMsg.INFO_START, LocalLLM.__name__,'')
#         try:
#             # Базовые значения параметров
#             temp = GeneralValuesLLM.GEN_RESPONSE_TEMP
#             max_tokens = GeneralValuesLLM.GEN_RESPONSE_MAX_TOKENS
#             repetition_penalty = GeneralValuesLLM.GEN_RESPONSE_REPETITION_PENALTY
#             frequency_penalty = GeneralValuesLLM.GEN_RESPONSE_FREQUENCY_PENALTY

#             # Если переданы параметры модели, обновляем значения
#             if model_params is not None:
#                 temp = model_params.get("temperature", temp)
#                 max_tokens = model_params.get("max_new_tokens", max_tokens)
#                 repetition_penalty = model_params.get("repetition_penalty", repetition_penalty)
#                 frequency_penalty = model_params.get("frequency_penalty", frequency_penalty)
                
#             data = {"inputs": prompt_input,
#                     "parameters": {
#                         "top_k": GeneralValuesLLM.GEN_RESPONSE_TOP_K,
#                         "top_n_tokens": GeneralValuesLLM.GEN_RESPONSE_TOP_N_TOKENS,
#                         "top_p": GeneralValuesLLM.GEN_RESPONSE_TOP_P,
#                         "temperature": temp,
#                         "max_new_tokens": max_tokens,
#                         "frequency_penalty": frequency_penalty,
#                         "do_sample": True,
#                         "repetition_penalty": repetition_penalty,
#                     }
#                     }

#             response = requests.post(
#                 url=self.host,
#                 headers=self.headers,
#                 json=data,
#                 timeout=60
#             )
#             answer = response.json()[Keys.GENERATED_TEXT]

#             LOGGER.info(LoggerMsg.INFO_END, LocalLLM.__name__, answer[:30])
                       
#             if response.status_code == 200:
#                 return answer
#         except Exception as error:
#             raise

#     def stream_complete(self, prompt: str, **kwargs):
#         """Потоковая генерация не поддерживается."""
#         raise NotImplementedError(LoggerMsg.NOT_IMPLEMENTED)

#     @property
#     def metadata(self) -> LLMMetadata:
#         """Возвращает метаданные о модели."""
#         return LLMMetadata(model_name=GeneralUtilitsConsts.MODEL_LOCAL_NAME)
