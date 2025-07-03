import re
import streamlit as st
from src.logger import LOGGER
from src.models import (AppSettingsParamConfig, ModelParamsConfig)
from src.wiki import WikiClient
from typing import Union, Dict
from src.text_constants import (AppSettings, LoggerMsg)


def render_param_slider(param_data: AppSettingsParamConfig, session_state_key: str) -> Union[float, int]:
    options = param_data.options
    st.subheader(param_data.label.format(''))
    with st.expander(AppSettings.EXPANDER, expanded=False):
        st.write(param_data.description)
    value = st.slider(
            label=param_data.label.format(param_data.default),
            min_value=options.start,
            max_value=options.stop,
            value=param_data.default,
            step=options.step,
            format=f"%.{options.decimals}f"
        )
    st.session_state[session_state_key] = value
    return value

def reset_params_to_default(params_config: ModelParamsConfig) -> Dict[str, Union[float, int]]:
    default_values = {k: v.default for k, v in params_config.__dict__.items()}
    return default_values

def is_http_url(text: str) -> bool:
    return re.search(r"https?://", text) is not None

def is_wiki_url(text: str) -> bool:
    LOGGER.info(LoggerMsg.INFO_START, is_wiki_url.__name__,'')
    if is_http_url(text) and len(text) < 100:
        try:
            LOGGER.info(LoggerMsg.INFO_START, WikiClient.__name__,'')
            wc = WikiClient()
            description = wc.get_wiki_scenario(text)
            LOGGER.info(LoggerMsg.INFO_END, WikiClient.__name__,'')
            return description
        except Exception as e:
            st.error(f"Ошибка при загрузке сценария: {e}")
            LOGGER.error(LoggerMsg.ERROR_WIKI_GET_SCENARIO, WikiClient.__name__,'')
            description = text
            return description
    else:
        LOGGER.info(LoggerMsg.INFO_END, is_wiki_url.__name__,'')
        description = text
        return description
