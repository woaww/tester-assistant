from typing import List, Optional
from pydantic import BaseModel
from enum import Enum
from src.text_constants import (ROLE_USER, ROLE_ASSISTANT)

class RoleEnum(str, Enum):
    USER = ROLE_USER
    ASSISTANT = ROLE_ASSISTANT

class ChatMessage(BaseModel):
    """Модель для одного сообщения в чате"""    
    role: RoleEnum
    content: str
    rating: Optional[str] = None

class AppSettingsParamConfig(BaseModel):
    """Модель для одного UI-параметра"""
    label: str
    description: str
    select: str
    options: List[float] | List[int]
    default: float | int

class ModelParamsConfig(BaseModel):
    """Содержит все параметры в виде полей типа AppSettingsParamConfig"""
    temperature: AppSettingsParamConfig
    max_new_tokens: AppSettingsParamConfig
    repetition_penalty: AppSettingsParamConfig
    frequency_penalty: AppSettingsParamConfig

class PagesApp(BaseModel):
    title_main_page: str
    page_home: str

class ModelParams(BaseModel):
    """Хранит реальные значения, выбранные пользователем через интерфейс"""
    temperature: float
    max_new_tokens: int
    repetition_penalty: float
    frequency_penalty: float

    @classmethod
    def init_params(cls, defaults: dict) -> "ModelParams":
        return cls(**defaults)
    
# class InputDataModel(BaseModel):
#     method: str
#     endpoint: str
#     base_url: str = "DEFAULT_BASE_URL_VALUE"  # Установите значение по умолчанию, если это необходимо
#     count: int = 1  # Установите значение по умолчанию, если это необходимо
