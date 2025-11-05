from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field
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
    project_id: str = UtilitsParsing.PROJECT_ID
    parent_id: str = UtilitsParsing.SECTION_TESTIT
    name: str = "TestIt"

class ProjectSearchResponse(BaseModel):
    id: str
    globalId: str
    name: str

class StepModel(BaseModel):
    action: str
    expected: Optional[str] = None

class TagModel(BaseModel):
    name: str

class TestCaseCreateModel(BaseModel):
    project_id: str = UtilitsParsing.PROJECT_ID
    section_id: str
    name: str
    steps: List[Dict[str, Optional[str]]] = []
    precondition_steps: List[Dict[str, Optional[str]]] = [] 
    postcondition_steps: List[Dict[str, Optional[str]]] = []
    expected_result: Optional[str] = None
    priority: str = "Medium"
    state: str = "NeedsWork"
    duration: int = 60
    tags: List[TagModel] = Field(default_factory=lambda: [TagModel(name="ai-assistant")])
    links: List[dict] = []
    attributes: dict = {}

class ApiKwargs(BaseModel):
    spec_url: str
    spec_path: str
    spec_method: str
    type: str
    new_cases: bool = False
    language: str = ""

    def __init__(self, 
                 spec_url: str, 
                 type: str,
                 spec_path: str = "", 
                 spec_method: bool = False,
                 new_cases: bool = False,
                 language: str = ""):
        super().__init__(
            spec_url=spec_url,
            type=type,
            spec_path=spec_path,
            spec_method=spec_method, 
            new_ases=new_cases,
            language=language,
        )

class WikiJiraKwargs(BaseModel):
    source_type: str = ""
    description_text: str = ""
    new_cases: bool = False

    def __init__(self, 
                 source_type: str = "", 
                 description_text: str = "", 
                 new_cases: bool = False):
        super().__init__(
            source_type=source_type,
            description_text=description_text,
            new_cases=new_cases
        )