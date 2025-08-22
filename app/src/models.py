from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel#, Field
from .text_constants import UtilitsParsing


class FunctionCallLog(BaseModel):
    function: str
    # args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

class FunctionResultLog(BaseModel):
    function: str
    execution_time: Union[int, float]  # в секундах
    # result: Any

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

class SectionCreateModel(BaseModel):
    project_id: str
    parent_id: str = UtilitsParsing.SECTION_TESTIT
    name: str

class ProjectSearchResponse(BaseModel):
    id: str
    globalId: str
    name: str

class StepModel(BaseModel):
    action: str
    expected: Optional[str] = None

class TestCaseCreateModel(BaseModel):
    project_id: str
    section_id: str
    name: str
    steps: List[Dict[str, Optional[str]]] = []
    precondition_steps: List[Dict[str, Optional[str]]] = [] 
    postcondition_steps: List[Dict[str, Optional[str]]] = []
    expected_result: Optional[str] = None
    priority: str = "Medium"
    state: str = "NeedsWork"
    duration: int = 60
    tags: List[str] = []
    links: List[dict] = []
    attributes: dict = {}