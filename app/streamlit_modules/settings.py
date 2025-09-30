import re
import streamlit as st
from typing import Dict, Union
from src.wiki import WikiClient
from src.jira_client import JiraClient
from src.models import AppSettingsParamConfig, ModelParamsConfig
from src.text_constants import AppSettings
from src.logger import log_function_call


def render_param_slider(param_data: AppSettingsParamConfig,
                        session_state_key: str) -> Union[float, int]:
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


@log_function_call()
def reset_params_to_default(params_config: ModelParamsConfig) -> Dict[str, Union[float, int]]:
    default_values = {k: v.default for k, v in params_config.__dict__.items()}
    return default_values

@log_function_call()
def is_http_url(text: str) -> bool:
    return re.search(r"https?://", text) is not None

@log_function_call()
def extract_url(input_string, http_flag=True):
    cleaned_string = re.sub(r'[а-яА-Я]', '', input_string)

    cleaned_string = ' '.join(cleaned_string.split())

    if http_flag:
        # Извлекаем URL
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        url = url_pattern.search(cleaned_string)

        return url.group(0) if url else None
    else:
        return cleaned_string

@log_function_call()
def is_wiki_url(text_old: str) -> bool:

    if is_http_url(text_old):
        text = extract_url(text_old)
        wc = WikiClient()
        description = wc.get_wiki_scenario(text)
        return description
    else:
        description = text_old
        return description

@log_function_call()
def is_jira_url(text_old: str) -> str:

    if is_http_url(text_old):
        try:
            text = extract_url(text_old)
            jc = JiraClient()
            ticket_id = jc.extract_ticket_id(text)
            description = jc.get_issue_description(ticket_id)
            return {"description": description}
        except Exception as e:
            st.error(f"Ошибка при загрузке сценария Jira")

