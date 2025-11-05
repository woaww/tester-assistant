import streamlit as st
from functools import partial
from streamlit_modules.session_manager import (init_session, get_api_cases,)
from streamlit_modules.settings import (render_param_slider, is_wiki_url,
                                        is_jira_url, reset_params_to_default)
from src.text_constants import AppSettings, APP_SIDE_PANEL_PARAMS
from src.models import ModelParamsConfig, ApiKwargs, WikiJiraKwargs
from streamlit_modules.widgets import *
from src.utils import  split_api_test_cases

# --- Инициализация ---
init_session()
model_params_config = ModelParamsConfig(**APP_SIDE_PANEL_PARAMS)

# Основная панель
st.set_page_config(page_title=AppSettings.PAGE_HOME, layout="centered")


with st.container():
    st.title(AppSettings.PAGE_HOME)

        # --- Боковая панель ---
    with st.sidebar:
        st.header(AppSettings.PAGE_HOME)
        params_config = model_params_config

        # Инициализация параметров в session_state при первом запуске
        if 'model_params' not in st.session_state:
            st.session_state.model_params = reset_params_to_default(params_config)

        params_dict = {}
        for param_name, param_data in params_config.__dict__.items():
            session_state_key = f"param_{param_name}"
            value = render_param_slider(param_data, session_state_key)
            params_dict[param_name] = value

        st.session_state.model_params.update(params_dict)

    OPTIONS = st.selectbox(AppSettings.ST_SELECTBOX, AppSettings.OPTIONS_LIST)

    with st.container():
        match OPTIONS:
            case AppSettings.TYPE_OPTION_WIKI:
                st.subheader(AppSettings.TYPE_OPTION_WIKI)
                url_or_text = st.text_input("Введите URL страницы Вики")

                description_text = is_wiki_url(url_or_text)

                if description_text in ["", None]:
                    st.session_state.jira_wiki_error_message = "Введите URL страницы Вики"
                    st.warning(st.session_state.jira_wiki_error_message)
                else:
                    kwargs_for_wiki = WikiJiraKwargs("wiki",description_text)

                    on_click_with_args_wiki = partial(button_jira_wiki_get_test_case, 
                                                    kwargs_for_wiki)

                # Кнопка для генерации тест-кейсов (перезапись)
                st.button(
                    label=AppSettings.BUTTON_GET_CASES,
                    on_click=on_click_with_args_wiki
                )

                if 'jira_wiki_error_message' in st.session_state:
                    st.warning(st.session_state.jira_wiki_error_message)
                    del st.session_state.jira_wiki_error_message

                if 'wiki_test_cases_response' in st.session_state:
                    st.markdown(st.session_state.wiki_test_cases_response)

                # Кнопка для генерации дополнительных тест-кейсов (отображается только если тест-кейсы уже сгенерированы)
                    kwargs_for_wiki_new = kwargs_for_wiki.model_copy(update={"new_cases": True})
                    on_click_with_args_wiki_new = partial(button_jira_wiki_get_test_case, 
                                                kwargs_for_wiki_new)
                    st.button(
                        label="Сгенерировать дополнительные тестовые кейсы (Вики)",
                        on_click=on_click_with_args_wiki_new
                    )
                
                    # === Отправить в TestIt, источник и фидбэк ==
                    st.button(
                        label="Отправить комментарий к задаче в Вики",
                        on_click=add_comment_to_page,
                        kwargs={'url': url_or_text, 
                                'comment_body': st.session_state.wiki_test_cases_response}
                    )

                    new_section_name = st.text_input("Введите название секции для TestIt'а")
                    st.button(
                        "Отправить кейсы в TestIt",
                        on_click=send_to_testit,
                        kwargs={"new_section_name": new_section_name, 
                                "source_type": "wiki"}
                    )

                    save_response_and_get_feedback(
                            url=url_or_text,
                            response = st.session_state.wiki_test_cases_response
                        )

            case AppSettings.TYPE_OPTION_CURL:

                st.subheader(AppSettings.TYPE_OPTION_CURL)

                spec_url = st.text_input("Введите URL спецификации API",
                                        value = AppSettings.DSCR_BASE_URL_VALUE)
                spec_path = st.text_input("Введите нужный path",
                                            value = AppSettings.DSCR_BASE_PATH_VALUE)
                spec_method = st.text_input("Введите метод",
                                            value = AppSettings.DSCR_BASE_METHOD_VALUE)
                
                kwargs_for_api = ApiKwargs(spec_url, "api", spec_path, spec_method)

                on_click_with_args_api = partial(button_api_get_test_case, 
                                                kwargs_for_api)
                
                if not spec_path or spec_url or spec_method:
                        st.warning("Введите URL спецификации API, нужный path и метод")
                else:
                    st.button("Сгенерировать тестовые кейсы в формате curl",
                            on_click=on_click_with_args_api)

                    if getattr(st.session_state, 'api_error_message', None):
                        st.warning(st.session_state.api_error_message)

                    if getattr(st.session_state, 'api_test_cases_response', None):
                        st.markdown(split_api_test_cases(get_api_cases()))

                        # Кнопка для генерации дополнительных тест-кейсов
                        kwargs_for_api_new = kwargs_for_api.model_copy(update={"new_cases":True})

                        on_click_with_args_api_new = partial(button_api_get_test_case, 
                                                kwargs_for_api_new)
                        
                        st.button("Сгенерировать дополнительные тестовые кейсы (API)",
                            on_click=on_click_with_args_api_new)
                        
                        save_response_and_get_feedback(
                            url=spec_url,
                            response = st.session_state.api_test_cases_response,
                            path=spec_path,
                            method=spec_method,
                        )

                # --- перевод на другие языки ---

                language = st.selectbox("Выберите язык для преобразования тест-кейсов",
                                        ["Java + RestAssured", "Python + Requests (pytest)"])
                
                upd_kwargs_for_api = kwargs_for_api.model_copy(update={"type": "translate_test_cases",
                                                            "new_cases":False, 
                                                            "language": language})
                
                on_click_with_args_api_upd = partial(button_api_get_test_case, 
                                                upd_kwargs_for_api)
                
                st.button("Преобразовать тестовые кейсы",
                    on_click=on_click_with_args_api_upd)
                
                if getattr(st.session_state, 'translated_test_cases_response', None):
                        st.markdown(st.session_state.translated_test_cases_response)


            case AppSettings.TYPE_OPTION_JIRA:
                st.subheader(AppSettings.TYPE_OPTION_JIRA)
                jira_url = st.text_input("Введите URL страницы Jira")


                description_text = is_jira_url(jira_url)

                if description_text in ["", None]:
                    st.session_state.jira_wiki_error_message = "Введите URL страницы Jira"
                    st.warning(st.session_state.jira_wiki_error_message)
                else:
                    kwargs_for_jira = WikiJiraKwargs("jira",description_text)

                    on_click_with_args_jira_upd = partial(button_jira_wiki_get_test_case, 
                                                    kwargs_for_jira)

                # Кнопка для генерации тест-кейсов (перезапись)
                st.button(
                    label=AppSettings.BUTTON_GET_CASES,
                    on_click=on_click_with_args_jira_upd)

                if 'jira_wiki_error_message' in st.session_state:
                    st.warning(st.session_state.jira_wiki_error_message)
                    del st.session_state.jira_wiki_error_message

                if 'jira_test_cases_response' in st.session_state:
                    st.markdown(st.session_state.jira_test_cases_response)

                # Кнопка для генерации дополнительных тест-кейсов (отображается только если тест-кейсы уже сгенерированы)
                    kwargs_for_jira_new = kwargs_for_jira.model_copy(update={"new_cases":True})

                    on_click_with_args_jira_new = partial(button_jira_wiki_get_test_case, 
                                                kwargs_for_jira_new)

                    st.button(
                        label="Сгенерировать дополнительные тестовые кейсы (Вики)",
                        on_click=on_click_with_args_jira_new)
                
                    # === Отправить в TestIt, источник и фидбэк ==

                    new_section_name = st.text_input("Введите название секции для TestIt'а")
                    st.button(
                        "Отправить кейсы в TestIt",
                        on_click=send_to_testit,
                        kwargs={"new_section_name": new_section_name, 
                                "source_type": "jira"}
                    )

                    st.button(
                        label="Отправить комментарий к задаче в Jira",
                        on_click=add_comment_to_issue,
                        kwargs={'url': jira_url, 
                                'comment_body': st.session_state.jira_test_cases_response}
                    )

                    save_response_and_get_feedback(
                            url=jira_url,
                            response = st.session_state.jira_test_cases_response
                        )
