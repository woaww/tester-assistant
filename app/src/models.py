from typing import Any, Dict, Optional, Union

from pydantic import BaseModel


class FunctionCallLog(BaseModel):
    function: str
    kwargs: Dict[str, Any]


class FunctionResultLog(BaseModel):
    function: str
    execution_time: Union[int, float]


class FunctionErrorLog(BaseModel):
    function: str
    error: str
    traceback: str
    call: Optional[Dict[str, Any]] = None


class Options(BaseModel):
    start: Union[float, int]
    stop: Union[float, int]
    step: Union[float, int]
    decimals: int


class AppSettingsParamConfig(BaseModel):
    label: str
    description: str
    select: str
    options: Options
    default: Union[float, int]


class ModelParamsConfig(BaseModel):
    temperature: AppSettingsParamConfig
    max_new_tokens: AppSettingsParamConfig
    repetition_penalty: AppSettingsParamConfig
    frequency_penalty: AppSettingsParamConfig