from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field


class Options(BaseModel):
    start: Union[float, int]
    stop: Union[float, int]
    step: Union[float, int]
    decimals: int

class AppSettingsParamConfig(BaseModel):
    """Модель для одного UI-параметра"""
    label: str
    description: str
    select: str
    options: Options
    default: Union[float, int]

class ModelParamsConfig(BaseModel):
    """Содержит все параметры в виде полей типа AppSettingsParamConfig"""
    temperature: AppSettingsParamConfig
    max_new_tokens: AppSettingsParamConfig
    repetition_penalty: AppSettingsParamConfig
    frequency_penalty: AppSettingsParamConfig

class ModelParams(BaseModel):
    temperature: float
    max_new_tokens: int
    repetition_penalty: float
    frequency_penalty: float