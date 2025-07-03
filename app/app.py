import streamlit as st
from streamlit_modules.session_manager import (init_session, get_wiki_cases, 
                                               get_api_cases, add_case, is_unique)
from generate_modules.test_case_generator import (generate_wiki_test_cases, generate_api_test_cases)
from src.specification_api import SpecificationParser
from src.text_constants import AppSettings, APP_SIDE_PANEL_PARAMS
from src.models import ModelParamsConfig#, ModelParams
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
#TODO: смержить все кейсы в один вывод

st.title(AppSettings.PAGE_HOME)
OPTIONS = st.selectbox(AppSettings.ST_SELECTBOX, AppSettings.OPTIONS_LIST)

match OPTIONS:
    case AppSettings.TYPE_OPTION_WIKI:
        st.subheader(AppSettings.TYPE_OPTION_WIKI)
        url_or_text = st.text_area("Введите описание задачи или URL страницы Вики")

        description_text = is_wiki_url(url_or_text)

        if st.button(AppSettings.BUTTON_GET_CASES):
            if not description_text:
                st.warning("Введите описание задачи")
            else:
                with st.spinner(AppSettings.SPINNER):
                    model_params = st.session_state.model_params

                    response = generate_wiki_test_cases(
                        description=description_text,
                        model_params=model_params)
                    
                    add_case(response, case_type='wiki')
                    # new_cases = [line.strip("- ").strip() for line in response.splitlines() if line.startswith("- ")]
                    # print(new_cases)
                    # print(model_params)
                    # print(new_cases)
                    # unique_cases = [new_cases[0]]

                    # Добавляем в session_state только уникальные
                    # for case in new_cases:
                    #     add_case(case, case_type='wiki')
                        # add_case = {"id": len(get_wiki_cases()) + 1, "description": case}
                        # 
                        # if is_unique(case, case_type='wiki'):
                        #     print('UNIQUE CASE:', case)
                        #     unique_cases.append(case)
                    
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
                        # test_type="wiki",
                        description=description_text,
                        model_params=model_params)
                    add_case(response, case_type='wiki')
                    # new_cases = [line.strip("- ").strip() for line in response.splitlines() if line.startswith("- ")]
                    # print(new_cases)
                    # unique_cases = [new_cases[0]]

                    # Добавляем в session_state только уникальные
                    # for case in new_cases:
                        # add_cases = {"id": len(get_wiki_cases()) + 1, "description": case}
                        # add_case(case, case_type='wiki')
                        # if is_unique(case, case_type='wiki'):
                        #     print('UNIQUE CASE:', case)
                        #     unique_cases.append(case)
                    
                    # Отображаем результат
                    st.markdown(split_wiki_tests_by_separator(get_wiki_cases()))

    case AppSettings.TYPE_OPTION_CURL:
        st.subheader(AppSettings.TYPE_OPTION_CURL)
        spec_url = st.text_input("Введите URL спецификации API", 
                                 value = AppSettings.DSCR_BASE_URL_VALUE)

        if st.button("Сгенерировать тестовые кейсы в формате curl"):
            if not spec_url:
                st.warning("Введите URL спецификации API")
            else:
                try:
                    parser = SpecificationParser(spec_url)
                    spec_description = parser.parse_specification()
                    with st.spinner(AppSettings.SPINNER):
                        model_params = st.session_state.model_params
                        response = generate_api_test_cases(
                            description=spec_description,
                            url_ref = spec_url,
                            model_params=model_params
                        )
                        add_case(response, case_type='api')
                        # new_cases = [line.strip("- ").strip() for line in response.splitlines() if line.startswith("- ")]
                        # unique_cases = []

                        # Добавляем в session_state только уникальные
                        # for case in new_cases:
                            # new_case = {"id": len(get_api_cases()) + 1, "description": case}
                            # add_case(case, case_type='api')
                            # if is_unique(case, case_type='api'):
                            #     unique_cases.append(case)

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
                    spec_description = parser.parse_specification()
                    with st.spinner("Генерация дополнительных тестовых кейсов..."):
                        model_params = st.session_state.model_params

                        response = generate_api_test_cases(
                            description=spec_description,
                            url_ref = spec_url,
                            model_params=model_params
                        )
                        add_case(response, case_type='api')
                        # new_cases = [line.strip("- ").strip() for line in response.splitlines() if line.startswith("- ")]
                        # unique_cases = []

                        # Добавляем в session_state только уникальные
                        # for case in new_cases:
                            # new_case = {"id": len(get_api_cases()) + 1, "description": case}
                            # add_case(case, case_type='api')
                            # if is_unique(case, case_type='api'):
                            #     unique_cases.append(case)

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


# ---  Сворачиваемый контейнер для тест-кейсов ---
# with st.container():
#     st.subheader("Сгенерированные тест-кейсы")
#     wiki_cases = get_wiki_cases()
#     api_cases = get_api_cases()

#     with st.expander("Тест-кейсы из Вики", expanded=False):
#         if not wiki_cases:
#             st.info("Нет сгенерированных тест-кейсов для Вики.")
#         else:
#             for case in wiki_cases:
#                 st.write(f"ID: {case['id']} — Описание: {case['description']}")

#     with st.expander("Тест-кейсы для API", expanded=False):
#         if not api_cases:
#             st.info("Нет сгенерированных тест-кейсов для API.")
#         else:
#             for case in api_cases:
#                 st.write(f"ID: {case['id']} — Описание: {case['description']}")