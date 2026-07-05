"""
Общие элементы и хуки веб-интерфейса (Streamlit).

Содержит: инициализацию сессии, заголовки секций, виджеты параметров LLM в сайдбаре.
"""

from __future__ import annotations

from typing import Dict, Union

import streamlit as st

from src.logger import log_function_call
from src.models import AppSettingsParamConfig, ModelParamsConfig


def init_session() -> None:
    """Точка расширения для начального состояния session_state."""
    pass


def section_label(text: str) -> None:
    """Единообразная подпись секции страницы."""
    st.caption(text.upper())


def render_param_slider(
    param_data: AppSettingsParamConfig,
    session_state_key: str,
) -> Union[float, int]:
    """Слайдер одного параметра генерации LLM с подсказкой."""
    options = param_data.options
    current_value = st.session_state.get(session_state_key, param_data.default)
    value = st.slider(
        label=param_data.label.format(current_value),
        min_value=options.start,
        max_value=options.stop,
        value=current_value,
        step=options.step,
        format=f"%.{options.decimals}f",
        help=param_data.description,
    )
    st.session_state[session_state_key] = value
    return value


@log_function_call()
def reset_params_to_default(params_config: ModelParamsConfig) -> Dict[str, Union[float, int]]:
    return {k: v.default for k, v in params_config.__dict__.items()}
