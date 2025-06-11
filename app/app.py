# import re
# import streamlit as st
# from src.processing import *
# from streamlit_modules.chat_logic import initialize_chat, display_chat, process_user_input
# from streamlit_modules.settings import display_settings

# App title
# st.set_page_config(page_title="🤗💬 Ассистент тестировщиков")

# # Инициализация состояния страницы
# if "page" not in st.session_state:
#     st.session_state.page = "main"


# # Обработка навигации
# if st.session_state.page == "main":
#     ()
# elif st.session_state.page == "":
#     ()
# elif st.session_state.page == "":
#     ()

import streamlit as st
from streamlit_modules.session_manager import *
from streamlit_modules.widgets import *
from generate_modules.test_case_generator import choose_generate_response
from generate_modules.llama_index_integration import *
from src.wiki import WikiClient
from src.utils import *
from src.text_constants import *
from src.models import *
from src.ui_config import *
from src.logger import LOGGER

# import yaml

# --- Боковая панель ---
with st.sidebar:
    st.header(TITLE_MAIN_PAGE)
    params_config = get_full_params_config()

    params_dict = {}
    for param_name, param_data in params_config:
        value = render_param_slider(param_data)
        params_dict[param_name] = value

    model_params = ModelParams(**params_dict)
    st.session_state.model_params = model_params

# --- Основная панель ---

# st.set_page_config(page_title=TITLE_MAIN_PAGE)

st.title(TITLE_MAIN_PAGE)

init_session_state()
# existing_cases=get_test_cases()

# Выбор функции
OPTIONS = st.selectbox(ST_SELECTBOX, OPTIONS_LIST)

match OPTIONS:
    case "Генерация тестового кейса из сценария задачи (Вики)":
        st.subheader(TYPE_OPTION_WIKI)
        st.text(ST_INFO_WORK)
        # st.subheader("Ввод токенов")
        display_input_tokens(wiki=True)
        
        # Ввод количества кейсов
        count = st.number_input(NUMBER_OF_CASES, min_value=1, value=1, step=1)
        description = st.text_area(ST_INFO_ENTER_TEXT_LINK)
        
        wc = WikiClient(token=st.session_state.wiki_token)
        description = wc.get_wiki_scenario(description) if PATTERN_URL_IN_HTTP in description else description
        
        if st.button(BUTTON_GET_CASES):
            LOGGER.info(LOGGER_INFO_START, BUTTON_GET_CASES)
            if not description:
                st.warning(ST_WARNING_MSG_WIKI)
            elif not check_wiki_token(st.session_state.wiki_token):
                st.warning(ST_WARNING_MSG_WIKI)
            else:
                with st.spinner(SPINNER):
                    response = choose_generate_response(
                                type = TYPE_PROMPT_WIKI,
                                description=description, 
                                count=count,
                                existing_cases=get_test_cases(),
                                temperature=st.session_state.model_params.temperature,
                                max_new_tokens=st.session_state.model_params.max_new_tokens,
                                repetition_penalty=st.session_state.model_params.repetition_penalty,
                                frequency_penalty=st.session_state.model_params.frequency_penalty)
                    st.markdown(response)

        if st.button(BUTTON_GET_MORE_CASES):
            LOGGER.info(LOGGER_INFO_START, BUTTON_GET_MORE_CASES)
            if not description:
                st.warning(ST_WARNING_PLEASE_ENTER_DSCR)
            else:
                with st.spinner(SPINNER):
                    response = choose_generate_response(
                                type = TYPE_PROMPT_WIKI,
                                description=description, 
                                count=count, 
                                generate_more=True,
                                existing_cases=get_test_cases(),
                                temperature=st.session_state.model_params.temperature,
                                max_new_tokens=st.session_state.model_params.max_new_tokens,
                                repetition_penalty=st.session_state.model_params.repetition_penalty,
                                frequency_penalty=st.session_state.model_params.frequency_penalty)
                    st.markdown(response)

            if st.button(ST_REMOVED_TOKENS):
                display_delete_tokens()

    case "Генерация тестовых кейсов API (CURL)":
        st.subheader(TYPE_OPTION_CURL)
        
        method = st.text_input(DSCR_METHOD)
        endpoint = st.text_input(DSCR_ENDPOINT)
        base_url = st.text_input(DSCR_BASE_URL, value=DSCR_BASE_URL_VALUE) 
        count = st.number_input(DSCR_COUNT, min_value=1, value=1, step=1)
        
        if st.button(BUTTON_GET_CASES_CURL):
            LOGGER.info(LOGGER_INFO_START, BUTTON_GET_CASES_CURL)
            if not method or not endpoint:
                st.warning(ST_WARNING_PLEASE_ENTER)
            else:
                with st.spinner(SPINNER):
                    response = choose_generate_response(
                                type = TYPE_PROMPT_CURL,
                                method=method, 
                                endpoint=endpoint, 
                                base_url=base_url,
                                count=count,
                                existing_cases=get_test_cases(),
                                temperature=st.session_state.model_params.temperature,
                                max_new_tokens=st.session_state.model_params.max_new_tokens,
                                repetition_penalty=st.session_state.model_params.repetition_penalty,
                                frequency_penalty=st.session_state.model_params.frequency_penalty)
                    st.code(response, language=LANGUAGE_BASH)
            LOGGER.info(LOGGER_INFO_END, BUTTON_GET_CASES_CURL)
            if st.button(BUTTON_GET_MORE_CASES_CURL):
                if not method or not endpoint:
                    st.warning(ST_WARNING_PLEASE_ENTER)
                else:
                    with st.spinner(SPINNER):
                        response = choose_generate_response(
                            type = TYPE_PROMPT_CURL,
                            method=method,
                            endpoint=endpoint,
                            base_url=base_url,
                            count=count,
                            generate_more=True,
                            existing_cases=get_test_cases(),
                            temperature=st.session_state.model_params.temperature,
                            max_new_tokens=st.session_state.model_params.max_new_tokens,
                            repetition_penalty=st.session_state.model_params.repetition_penalty,
                            frequency_penalty=st.session_state.model_params.frequency_penalty)
            
                        st.code(response, language=LANGUAGE_BASH)

    case "Генерация тестовых кейсов API (Java + RestAssured)":
        st.subheader(TYPE_OPTION_JAVA)
        
        method = st.text_input(DSCR_METHOD)
        endpoint = st.text_input(DSCR_ENDPOINT)
        base_url = st.text_input(DSCR_BASE_URL, value=DSCR_BASE_URL_VALUE) 
        count = st.number_input(DSCR_COUNT, min_value=1, value=1, step=1)

        if st.button(BUTTON_GET_CASES_JAVA):
            if not method or not endpoint:
                st.warning(ST_WARNING_PLEASE_ENTER)
            else:
                with st.spinner(SPINNER):
                    response = choose_generate_response(
                            type = TYPE_PROMPT_JAVA,
                            method=method, 
                            endpoint=endpoint, 
                            base_url=base_url,
                            count=count,
                            existing_cases=get_test_cases(),
                            temperature=st.session_state.model_params.temperature,
                            max_new_tokens=st.session_state.model_params.max_new_tokens,
                            repetition_penalty=st.session_state.model_params.repetition_penalty,
                            frequency_penalty=st.session_state.model_params.frequency_penalty)
                    st.code(response, language=LANGUAGE_JAVA)

            if st.button(BUTTON_GET_MORE_CASES_JAVA):
                if not method or not endpoint:
                    st.warning(ST_WARNING_PLEASE_ENTER)
                else:
                    with st.spinner(SPINNER):
                        response = choose_generate_response(
                            type = TYPE_PROMPT_JAVA,
                            method=method,
                            endpoint=endpoint,
                            base_url=base_url,
                            count=count,
                            generate_more=True,
                            existing_cases=get_test_cases(),
                            temperature=st.session_state.model_params.temperature,
                            max_new_tokens=st.session_state.model_params.max_new_tokens,
                            repetition_penalty=st.session_state.model_params.repetition_penalty,
                            frequency_penalty=st.session_state.model_params.frequency_penalty)
                        st.code(response, language=LANGUAGE_JAVA)

    case "Генерация тестовых кейсов API (Python + Requests)":
        st.subheader(TYPE_OPTION_PYTHON)
        
        method = st.text_input(DSCR_METHOD)
        endpoint = st.text_input(DSCR_ENDPOINT)
        base_url = st.text_input(DSCR_BASE_URL, value=DSCR_BASE_URL_VALUE) 
        count = st.number_input(DSCR_COUNT, min_value=1, value=1, step=1)
        
        if st.button(BUTTON_GET_CASES_PYTHON):
            if not method or not endpoint:
                st.warning(ST_WARNING_PLEASE_ENTER)
            else:
                with st.spinner(SPINNER):
                    response = choose_generate_response(
                            type = TYPE_PROMPT_PYTHON,
                            method=method, 
                            endpoint=endpoint, 
                            base_url=base_url,
                            count=count,
                            existing_cases=get_test_cases(),
                            temperature=st.session_state.model_params.temperature,
                            max_new_tokens=st.session_state.model_params.max_new_tokens,
                            repetition_penalty=st.session_state.model_params.repetition_penalty,
                            frequency_penalty=st.session_state.model_params.frequency_penalty)
                    st.code(response, language=LANGUAGE_PYTHON)
                
            if st.button(BUTTON_GET_MORE_CASES_PYTHON):
                if not method or not endpoint:
                    st.warning(ST_WARNING_PLEASE_ENTER)
                else:
                    with st.spinner(SPINNER):
                        response = choose_generate_response(
                            type = TYPE_PROMPT_PYTHON,
                            method=method,
                            endpoint=endpoint,
                            base_url=base_url,
                            count=count,
                            generate_more=True,
                            existing_cases=get_test_cases(),
                            temperature=st.session_state.model_params.temperature,
                            max_new_tokens=st.session_state.model_params.max_new_tokens,
                            repetition_penalty=st.session_state.model_params.repetition_penalty,
                            frequency_penalty=st.session_state.model_params.frequency_penalty)

                        st.code(response, language=LANGUAGE_PYTHON)
