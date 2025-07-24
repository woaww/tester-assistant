import streamlit as st
from streamlit_modules.session_manager import (init_session, get_wiki_cases, get_api_cases,
                                               get_jira_cases, get_jira_cases_generated,
                                               add_case, get_api_cases_generated)
from streamlit_modules.settings import (render_param_slider, is_wiki_url, is_http_url,
                                        is_jira_url, reset_params_to_default, is_api_url_method)
from generate_modules.test_case_generator import (generate_wiki_test_cases, generate_api_test_cases,
                                                  generate_jira_test_cases)
from src.text_constants import AppSettings, APP_SIDE_PANEL_PARAMS, Separatiors
from src.models import ModelParamsConfig
# from src.logger import LOGGER
from streamlit_modules.widgets import button_get_test_case
from src.utils import split_wiki_jira_tests_by_separator, split_api_test_cases

# --- Инициализация ---
init_session()
model_params_config = ModelParamsConfig(**APP_SIDE_PANEL_PARAMS)


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

# --- Основная панель ---

with st.container():
    st.title(AppSettings.PAGE_HOME)
    OPTIONS = st.selectbox(AppSettings.ST_SELECTBOX, AppSettings.OPTIONS_LIST)

match OPTIONS:
    case AppSettings.TYPE_OPTION_WIKI:
        st.subheader(AppSettings.TYPE_OPTION_WIKI)
        url_or_text = st.text_area("Введите URL страницы Вики")

        description_text = is_wiki_url(url_or_text)

        if st.button(AppSettings.BUTTON_GET_CASES):

            st.session_state.wiki_cases = []

            if not description_text:
                st.warning("Введите описание задачи")
            else:
                with st.spinner(AppSettings.SPINNER):
                    model_params = st.session_state.model_params

                    response = generate_wiki_test_cases(
                        description=description_text,
                        model_params=model_params)
                    
                    add_case(response, case_type='wiki')
                            
                    # Отображаем результат
                    st.markdown(split_wiki_jira_tests_by_separator(get_wiki_cases()))
                    
        # Кнопка для генерации дополнительных тест-кейсов
        if st.button("Сгенерировать дополнительные тестовые кейсы (Вики)"):
            if not description_text:
                st.warning("Введите описание задачи")
            else:
                with st.spinner("Генерация дополнительных тестовых кейсов..."):
                    model_params = st.session_state.model_params
                    response = generate_wiki_test_cases(
                        description=description_text,
                        model_params=model_params)
                    
                    rep_w_separator = Separatiors.sep_cases+response

                    add_case(rep_w_separator, case_type='wiki')
                
                    st.markdown(split_wiki_jira_tests_by_separator(get_wiki_cases()))

    case AppSettings.TYPE_OPTION_CURL:

        st.subheader(AppSettings.TYPE_OPTION_CURL)
        spec_url = st.text_input("Введите URL спецификации API",
                                value = AppSettings.DSCR_BASE_URL_VALUE)
        spec_method = st.text_input("Введите метод")

        res_url_method = is_api_url_method(spec_url, spec_method)
        
        # with st.expander("Тест-кейсы", expanded=True):
        if not spec_url:
                st.warning("Введите URL спецификации API и метод")
        else:
            if st.button("Сгенерировать тестовые кейсы в формате curl",
                    on_click=button_get_test_case,
                    kwargs={"spec_url": res_url_method["url"],
                            "spec_method": res_url_method["method"],
                            "type": "api",
                            "new_cases": False}):
                
                # Отображаем результат
                st.markdown(split_api_test_cases(get_api_cases()))

            if get_api_cases_generated:
                # Кнопка для генерации дополнительных тест-кейсов
                if st.button("Сгенерировать дополнительные тестовые кейсы (API)",
                    on_click=button_get_test_case,
                    kwargs={"spec_url": spec_url,
                            "spec_method": spec_method,
                            "type": "api",
                            "new_cases": True}):
                    
                    # Отображаем результат
                    st.markdown(split_api_test_cases(get_api_cases()))

        # --- перевод на другие языки ---
        language = st.selectbox("Выберите язык для преобразования тест-кейсов",
                                ["Java + RestAssured", "Python + Requests (pytest)"])
        if st.button("Преобразовать тестовые кейсы"):
            
            api_cases = get_api_cases()

            if not api_cases:
                st.warning("Сначала сгенерируйте тестовые кейсы в формате curl.")
            else:
                with st.spinner("Преобразование тестовых кейсов..."):

                    model_params = st.session_state.model_params
                    
                    response =  generate_api_test_cases(
                        description="\n".join(api_cases),
                        url_ref = spec_url,
                        model_params=model_params,
                        language=language
                    )

                    st.markdown(response)

    case AppSettings.TYPE_OPTION_JIRA:
        st.subheader(AppSettings.TYPE_OPTION_JIRA)
        jira_url = st.text_area("Введите URL страницы Jira")

        description_text = is_jira_url(jira_url)

        if st.button(AppSettings.BUTTON_GET_CASES):

            st.session_state.jira_cases = []

            if not description_text or not is_http_url(jira_url):
                st.warning("Введите корректный URL страницы Jira")
            else:
                with st.spinner(AppSettings.SPINNER):
                    model_params = st.session_state.model_params

                    response = generate_jira_test_cases(
                        description=description_text,
                        model_params=model_params
                    )
                    # LOGGER.info(response)

                    rep_w_separator = Separatiors.sep_cases+response

                    add_case(rep_w_separator, case_type='jira')
                    
                    st.session_state.jira_cases_generated = True
                    st.markdown(split_wiki_jira_tests_by_separator(get_jira_cases()))

        # Генерация дополнительных тест-кейсов
        if get_jira_cases_generated:
            if st.button("Сгенерировать дополнительные тестовые кейсы"):
                if not description_text or not is_http_url(jira_url):
                    st.warning("Введите корректный URL страницы Jira")
                else:
                    with st.spinner("Генерация дополнительных тестовых кейсов..."):
                        model_params = st.session_state.model_params
                        
                        response = generate_jira_test_cases(
                            description=description_text,
                            model_params=model_params
                        )
                        
                        rep_w_separator = Separatiors.sep_cases+response

                        add_case(rep_w_separator, case_type='jira')
                        st.markdown(split_wiki_jira_tests_by_separator(get_jira_cases()))
