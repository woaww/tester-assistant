import streamlit as st
from streamlit_modules.session_manager import (init_session, get_wiki_cases,
                                               get_api_cases, add_case)
from generate_modules.test_case_generator import (generate_wiki_test_cases, generate_api_test_cases)
from src.specification_api import SpecificationParser
from src.text_constants import AppSettings, APP_SIDE_PANEL_PARAMS, Separatiors
from src.models import ModelParamsConfig
from streamlit_modules.widgets import render_param_slider, reset_params_to_default, is_wiki_url
from src.utils import split_wiki_tests_by_separator, split_api_test_cases

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

st.title(AppSettings.PAGE_HOME)
OPTIONS = st.selectbox(AppSettings.ST_SELECTBOX, AppSettings.OPTIONS_LIST)

match OPTIONS:
    case AppSettings.TYPE_OPTION_WIKI:
        st.subheader(AppSettings.TYPE_OPTION_WIKI)
        url_or_text = st.text_area("Введите описание задачи или URL страницы Вики")

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
                    st.markdown(split_wiki_tests_by_separator(get_wiki_cases()))
                    
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
                
                    st.markdown(split_wiki_tests_by_separator(get_wiki_cases()))

    case AppSettings.TYPE_OPTION_CURL:
        st.subheader(AppSettings.TYPE_OPTION_CURL)
        spec_url = st.text_input("Введите URL спецификации API", 
                                 value = AppSettings.DSCR_BASE_URL_VALUE)
        spec_method = st.text_input("Введите метод")

        if st.button("Сгенерировать тестовые кейсы в формате curl"):

            st.session_state.api_cases = []

            if not spec_url:
                st.warning("Введите URL спецификации API")
            else:
                try:
                    parser = SpecificationParser(spec_url)
                    spec_description = parser.parse_specification(spec_method)
                    
                    with st.spinner(AppSettings.SPINNER):
                        model_params = st.session_state.model_params
                        response = generate_api_test_cases(
                            description=spec_description,
                            url_ref = spec_url,
                            spec_method=spec_method,
                            model_params=model_params
                        )

                        add_case(response, case_type='api')

                        # Отображаем результат
                        st.markdown(split_api_test_cases(get_api_cases()))

                except Exception as e:
                    st.error(f"Ошибка при обработке спецификации: {e}")

        # Кнопка для генерации дополнительных тест-кейсов
        if st.button("Сгенерировать дополнительные тестовые кейсы (API)"):
            if not spec_url:
                st.warning("Введите URL спецификации API")
            else:
                try:
                    parser = SpecificationParser(spec_url)
                    spec_description = parser.parse_specification(spec_method)

                    with st.spinner("Генерация дополнительных тестовых кейсов..."):
                        model_params = st.session_state.model_params

                        response = generate_api_test_cases(
                            description=spec_description,
                            url_ref = spec_url,
                            spec_method=spec_method,
                            model_params=model_params
                        )
                        rep_w_separator = Separatiors.sep_cases+response

                        add_case(rep_w_separator, case_type='api')

                        # Отображаем результат
                        st.markdown(split_api_test_cases(get_api_cases()))

                except Exception as e:
                    st.error(f"Ошибка при обработке спецификации: {e}")

        # --- перевод на другие языки ---
        language = st.selectbox("Выберите язык для преобразования тест-кейсов", 
                                ["Java + RestAssured", "Python + Requests"])
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
