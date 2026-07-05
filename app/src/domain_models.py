from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TextContent(BaseModel):
    ownText: str | None = None
    containsText: str | None = None


class ElementContext(BaseModel):
    tag: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    textContent: TextContent | None = None


class SiblingsContext(BaseModel):
    prev: ElementContext | None = None
    next: ElementContext | None = None


class ElementSnapshot(BaseModel):
    """
    Снимок данных об элементе, которые используются LLM для генерации локаторов.
    """

    element_id: str
    tag: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    textContent: TextContent | None = None
    parent: ElementContext | None = None
    siblings: SiblingsContext | None = None

    selector_group: str | None = None  # например: "button" или исходный CSS selector/tag


class LocatorCandidate(BaseModel):
    """
    Результат генерации LLM до валидации.
    """

    element_id: str
    xpath: str
    description: str = ""
    selenide_element: str | None = None

    # Для обратной связи/отладки
    raw_llm: str | None = None
    original_index: int | None = None


class LocatorValidation(BaseModel):
    exists: bool
    count: int = 0


class LocatorResult(LocatorCandidate):
    """
    Локатор после валидации (и возможно после исправления).
    """

    validation: LocatorValidation | None = None
    stage: Literal["generated", "fixed"] = "generated"


class RunMode(BaseModel):
    kind: Literal["by_tags", "by_description", "by_parent"]
    selectors: list[str] | None = None
    prompt_description: str | None = None
    parent_xpath: str | None = None


class AuthConfig(BaseModel):
    enabled: bool = False
    custom_instructions: str | None = None
    # username/password не сохраняем в run metadata


class LlmConfig(BaseModel):
    base_url: str
    chat_model: str
    tools_model: str
    browser_model: str
    temperature: float | None = None
    max_new_tokens: int | None = None
    repetition_penalty: float | None = None
    frequency_penalty: float | None = None


class RunTimings(BaseModel):
    browser_start_s: float | None = None
    auth_s: float | None = None
    collect_elements_s: float | None = None
    generate_locators_s: float | None = None
    validate_locators_s: float | None = None
    fix_locators_s: float | None = None
    total_s: float | None = None


class RunMetrics(BaseModel):
    total_elements: int = 0
    total_locators: int = 0
    valid_after_generation: int = 0
    invalid_after_generation: int = 0
    fixed_valid: int = 0
    still_invalid: int = 0

    accuracy: float | None = None
    fix_rate: float | None = None
    correctness: float | None = None


class LocatorRunMeta(BaseModel):
    run_id: str
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    mode: RunMode
    auth: AuthConfig = Field(default_factory=AuthConfig)
    llm: LlmConfig | None = None

    limits: dict[str, Any] = Field(default_factory=dict)
    timings: RunTimings = Field(default_factory=RunTimings)
    metrics: RunMetrics = Field(default_factory=RunMetrics)


class LocatorRunArtifacts(BaseModel):
    """
    То, что мы сохраняем в централизованное хранилище.
    """

    meta: LocatorRunMeta
    elements: list[ElementSnapshot] = Field(default_factory=list)
    locators: list[LocatorResult] = Field(default_factory=list)

