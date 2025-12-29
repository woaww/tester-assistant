import streamlit as st
from functools import partial
import pandas as pd
from streamlit_modules.session_manager import (login_callback, get_api_cases,logout_callback)
from streamlit_modules.settings import (render_param_slider, is_wiki_url,
                                        is_jira_url, reset_params_to_default)
from src.text_constants import AppSettings, APP_SIDE_PANEL_PARAMS
from src.models import ModelParamsConfig, ApiKwargs, WikiJiraKwargs
from streamlit_modules.widgets import *
from src.utils import  split_api_test_cases
from src.el_attr_workflow import (
    run_el_attr_workflow,
    DEFAULT_URL,
    AVAILABLE_SELECTORS,
    DEFAULT_SELECTORS,
)


def auth_page():
    st.title("Авторизация")

    email = st.text_input("Введите ваш email:", key="email_input")

    # Используем on_click для мгновенного выполнения логики
    st.button(
        "Войти",
        on_click=login_callback,
        args=(email,) # Передаем значение email в функцию коллбэка
    )
    # Сообщение об успехе или ошибке теперь нужно обрабатывать внутри самого коллбэка, 
    # либо полагаться на основную логику переключения страниц.

def main_page(model_params_config):
    st.title(f"Добро пожаловать, {st.session_state['user_email']}!")
    st.write("Это главная страница вашего приложения.")
    
    # Используем on_click для мгновенного выполнения логики выхода
    st.button("Выйти", on_click=logout_callback)
        
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
                # === Блок по работе с Wiki ===

                case AppSettings.TYPE_OPTION_WIKI:
                    st.subheader(AppSettings.TYPE_OPTION_WIKI)

                    # Форма для основной генерации тест-кейсов
                    with st.form(key="wiki_form"):
                        wiki_url = st.text_input("Введите URL страницы Вики")
                        submit_button = st.form_submit_button(label=AppSettings.BUTTON_GET_CASES)

                        if submit_button:
                            description_text = is_wiki_url(wiki_url)
                            if not description_text:
                                st.session_state.jira_wiki_error_message = "Введите корректный URL страницы Вики"
                            else:
                                kwargs_for_wiki = WikiJiraKwargs("wiki", description_text)
                                st.session_state.kwargs_for_wiki = kwargs_for_wiki
                                on_click_with_args_wiki = partial(button_jira_wiki_get_test_case, kwargs_for_wiki)
                                on_click_with_args_wiki()

                    # Отображаем предупреждение, если оно есть
                    if 'jira_wiki_error_message' in st.session_state:
                        st.warning(st.session_state.jira_wiki_error_message)
                        del st.session_state.jira_wiki_error_message

                    # Отображаем результат, если он есть
                    if 'wiki_test_cases_response' in st.session_state:
                        st.markdown(st.session_state.wiki_test_cases_response)

                        # Восстанавливаем kwargs, используя сохранённый текст
                        if 'kwargs_for_wiki' in st.session_state:
                            kwargs_for_wiki_new = st.session_state.kwargs_for_wiki
                            kwargs_for_wiki_new = kwargs_for_wiki_new.model_copy(update={"new_cases": True})
                            on_click_with_args_wiki_new = partial(button_jira_wiki_get_test_case, kwargs_for_wiki_new)

                            st.button(
                                label="Сгенерировать дополнительные тестовые кейсы (Вики)",
                                on_click=on_click_with_args_wiki_new,
                                key="btn_generate_more_cases"
                            )
                    
                        # === Отправить в TestIt, источник и фидбэк ===
                        # st.button(
                        #     label="Отправить комментарий к задаче в Вики",
                        #     on_click=add_comment_to_page,
                        #     kwargs={'url': wiki_url, 
                        #             'comment_body': st.session_state.wiki_test_cases_response}
                        # )

                        if st.button(
                            label="Отправить комментарий к задаче в Вики",
                            on_click=add_comment_to_page,
                            kwargs={'url': wiki_url, 
                                    'comment_body': st.session_state.wiki_test_cases_response}
                        ):
                                st.success("Комментарий отправлен!")

                        project_name = st.text_input("Введите название проекта для TestIt'а")
                        section_name = st.text_input("Введите название секции для TestIt'а")
                        new_section_name = st.text_input("Введите название новой секции для TestIt'а")
                        st.button(
                            "Отправить кейсы в TestIt",
                            on_click=send_to_testit,
                            kwargs={"project_name": project_name, 
                                    "section_name": section_name, 
                                    "new_section_name": new_section_name, 
                                    "source_type": "wiki"}
                        )

                        st.write("Пожалуйста, оцените ответ:")
                        feedback_widget(
                                url=wiki_url,
                                response = st.session_state.wiki_test_cases_response,
                                model_params=st.session_state.model_params,
                                user_email=st.session_state.user_email
                            )
                        
                # === Блок по работе с API ===
                case AppSettings.TYPE_OPTION_CURL:

                    st.subheader(AppSettings.TYPE_OPTION_CURL)

                    with st.form(key="api_form"):
                        spec_url = st.text_input(
                            "Введите URL спецификации API",
                            value=AppSettings.DSCR_BASE_URL_VALUE
                        )
                        spec_path = st.text_input(
                            "Введите нужный path",
                            value=AppSettings.DSCR_BASE_PATH_VALUE
                        )
                        spec_method = st.text_input(
                            "Введите метод",
                            value=AppSettings.DSCR_BASE_METHOD_VALUE
                        )
                        submit_button = st.form_submit_button(label="Сгенерировать тестовые кейсы в формате curl")

                        if submit_button:
                            if not spec_url or not spec_path or not spec_method:
                                st.session_state.api_error_message = "Введите URL спецификации API, нужный path и метод"
                            else:
                                kwargs_for_api = ApiKwargs(spec_url, "api", spec_path, spec_method)
                                st.session_state.kwargs_for_api = kwargs_for_api
                                on_click_with_args_api = partial(button_api_get_test_case, kwargs_for_api)
                                on_click_with_args_api()

                    # Отображаем предупреждение, если оно есть
                    if 'api_error_message' in st.session_state:
                        st.warning(st.session_state.api_error_message)
                        del st.session_state.api_error_message

                    # Отображаем результат, если он есть
                    if 'api_test_cases_response' in st.session_state:
                        st.markdown(split_api_test_cases(get_api_cases()))

                        # Восстанавливаем kwargs, используя сохранённый текст
                        if 'kwargs_for_api' in st.session_state:
                            kwargs_for_api_orig = st.session_state.kwargs_for_api
                            kwargs_for_api_new = kwargs_for_api_orig.model_copy(update={"new_cases": True})
                        # Кнопка для генерации дополнительных тест-кейсов
                        # kwargs_for_api_new = ApiKwargs(spec_url, "api", spec_path, spec_method, new_cases=True)
                            on_click_with_args_api_new = partial(button_api_get_test_case, kwargs_for_api_new)
                            st.button(
                                "Сгенерировать дополнительные тестовые кейсы (API)",
                                on_click=on_click_with_args_api_new
                            )

                        feedback_widget(
                            url=spec_url,
                            response=st.session_state.api_test_cases_response,
                            path=spec_path,
                            method=spec_method,
                            model_params=st.session_state.model_params,
                            user_email=st.session_state.user_email
                        )

                        # --- перевод на другие языки ---
                        language = st.selectbox("Выберите язык для преобразования тест-кейсов",
                                                ["Java + RestAssured", "Python + Requests"])
                        upd_kwargs_for_api = st.session_state.kwargs_for_api.model_copy(
                            update={
                                "type": "translate_test_cases",
                                "new_cases": False,
                                "language": language
                            }
                        )
                        # upd_kwargs_for_api = ApiKwargs(spec_url, "translate_test_cases", 
                        #                                spec_path, spec_method,
                        #                                False, language)
                        # upd_kwargs_for_api = kwargs_for_api.model_copy(update={"type": "translate_test_cases",
                        #                                             "new_cases":False, 
                        #                                             "language": language})
                        
                        on_click_with_args_api_upd = partial(button_api_get_test_case, 
                                                        upd_kwargs_for_api)
                        
                        st.button("Преобразовать тестовые кейсы",
                            on_click=on_click_with_args_api_upd)
                        
                        if getattr(st.session_state, 'translated_test_cases_response', None):
                                st.markdown(st.session_state.translated_test_cases_response)

                # === Блок по работе с Jira ===
                case AppSettings.TYPE_OPTION_JIRA:
                    st.subheader(AppSettings.TYPE_OPTION_JIRA)

                    with st.form(key="jira_form"):
                        jira_url = st.text_input("Введите URL страницы Jira")
                        submit_button = st.form_submit_button(label=AppSettings.BUTTON_GET_CASES)

                        if submit_button:
                            description_text = is_jira_url(jira_url)
                            if not description_text:  # проверяем на пустоту или None
                                st.session_state.jira_wiki_error_message = "Введите корректный URL страницы Jira"
                            else:
                                kwargs_for_jira = WikiJiraKwargs("jira", description_text)
                                st.session_state.kwargs_for_jira = kwargs_for_jira
                                on_click_with_args_jira = partial(button_jira_wiki_get_test_case, kwargs_for_jira)
                                on_click_with_args_jira()

                    # Отображаем предупреждение, если оно есть
                    if 'jira_wiki_error_message' in st.session_state:
                        st.warning(st.session_state.jira_wiki_error_message)
                        del st.session_state.jira_wiki_error_message

                    # Отображаем результат, если он есть
                    if 'jira_test_cases_response' in st.session_state:
                        st.markdown(st.session_state.jira_test_cases_response)

                        if 'kwargs_for_jira' in st.session_state:
                            kwargs_for_jira_new = st.session_state.kwargs_for_jira
                    # === Генерация дооплнительных тестовых кейсов ===
                    # Кнопка для генерации дополнительных тест-кейсов (отображается только если тест-кейсы уже сгенерированы)
                            kwargs_for_jira_new = kwargs_for_jira_new.model_copy(update={"new_cases":True})
                            on_click_with_args_jira_new = partial(button_jira_wiki_get_test_case, 
                                                        kwargs_for_jira_new)

                            st.button(
                                label="Сгенерировать дополнительные тестовые кейсы (Вики)",
                                on_click=on_click_with_args_jira_new,
                                key="btn_generate_more_cases_jira")
                    
                            # === Отправить в TestIt, источник и фидбэк ==
                            project_name = st.text_input("Введите название проекта для TestIt'а",)
                            section_name = st.text_input("Введите название секции для TestIt'а",)
                            new_section_name = st.text_input("Введите название новой секции для TestIt'а")
                            st.button(
                                "Отправить кейсы в TestIt",
                                on_click=send_to_testit,
                                kwargs={"project_name": project_name, 
                                        "section_name": section_name, 
                                        "new_section_name": new_section_name, 
                                        "source_type": "jira"}
                            )

                            # st.button(
                            #     label="Отправить комментарий к задаче в Jira",
                            #     on_click=add_comment_to_issue,
                            #     kwargs={'url': jira_url, 
                            #             'comment_body': st.session_state.jira_test_cases_response}
                            # )
                            if st.button(
                                label="Отправить комментарий к задаче в Jira",
                                on_click=add_comment_to_issue,
                                kwargs={'url': jira_url, 'comment_body': st.session_state.jira_test_cases_response}
                            ):
                                st.success("Комментарий отправлен!")


                            feedback_widget(
                                    url=jira_url,
                                    response = st.session_state.jira_test_cases_response,
                                    model_params=st.session_state.model_params,
                                    user_email=st.session_state.user_email
                                )

                case AppSettings.TYPE_OPTION_EL_ATTR:
                    st.subheader("Генератор XPath‑локаторов")

                    target_url = st.text_input(
                        "URL страницы",
                        value=DEFAULT_URL,
                    )

                    mode = st.radio(
                        "Режим",
                        options=("По тегам", "По описанию"),
                        horizontal=True,
                        key="el_attr_mode",
                    )

                    generate_selenide = st.checkbox(
                        "Сгенерировать SelenideElement",
                        value=False,
                        help="Оставьте выключенным, если нужны только XPath и описания",
                        key="el_attr_generate_selenide",
                    )

                    selected_selectors = []
                    prompt_description = ""

                    if mode == "По тегам":
                        selected_selectors = st.multiselect(
                            "Теги для анализа",
                            options=AVAILABLE_SELECTORS,
                            default=DEFAULT_SELECTORS,
                            help="По умолчанию: button, input.",
                            key="el_attr_selectors",
                        )
                    else:
                        prompt_description = st.text_input(
                            "Описание элемента (AI-поиск)",
                            placeholder="Например: зелёная кнопка 'Войти' в правом верхнем углу",
                            help="browser_use ищет один элемент по описанию и строит локатор",
                            key="el_attr_prompt_desc",
                        )

                    st.markdown("---")

                    def render_locator_panel(locators):
                        """
                        locators:
                          - либо list[str] (старый формат),
                          - либо list[dict] с полями 'xpath', 'exists', 'count', 'description' (новый формат).
                        """
                        st.markdown("**XPath‑локаторы**")

                        rows = []
                        if locators:
                            first = locators[0]
                            if isinstance(first, dict):
                                for item in locators:
                                    exists = item.get("exists")
                                    count = item.get("count")
                                    description = item.get("description", "")
                                    selenide_element = item.get("selenide_element", "—")

                                    if not exists:
                                        status_icon = "❌"
                                    else:
                                        if isinstance(count, int) and count > 1:
                                            status_icon = "⚠️"
                                        else:
                                            status_icon = "✅"

                                    rows.append(
                                        {
                                            "XPath": item.get("xpath", ""),
                                            "Описание": description if description else "—",
                                            "Статус": status_icon,
                                            "Кол-во элементов": count if count is not None else "?",
                                            "SelenideElement": selenide_element,
                                        }
                                    )
                            else:
                                for xpath in locators:
                                    rows.append(
                                        {
                                            "XPath": xpath,
                                            "Описание": "—",
                                            "Статус": "?",
                                            "Кол-во элементов": "?",
                                            "SelenideElement": "—",
                                        }
                                    )

                        locator_output = "\n".join(row["XPath"] for row in rows) if rows else ""

                        st.download_button(
                            label="Скачать .txt",
                            data=locator_output,
                            file_name="xpath_locators.txt",
                            mime="text/plain",
                        )

                        view_mode = st.radio(
                            "Отображение",
                            options=("Таблица", "Текст"),
                            horizontal=True,
                            key="locator_view_mode",
                        )

                        if view_mode == "Текст":
                            text_output = []
                            for row in rows:
                                xpath = row["XPath"]
                                description = row.get("Описание", "—")
                                selenide_line = row.get("SelenideElement", "—")
                                parts = [xpath]
                                if description and description != "—":
                                    parts.append(f"# {description}")
                                text_output.append("  ".join(parts))
                                if selenide_line and selenide_line != "—":
                                    text_output.append(selenide_line)
                            st.code("\n".join(text_output) if text_output else "—", language="text")
                        else:
                            locator_df = pd.DataFrame(rows or [{"XPath": "—", "Описание": "—", "Статус": "—", "Кол-во элементов": "—", "SelenideElement": "—"}])
                            locator_df.index = locator_df.index + 1
                            locator_df.index.name = "№"
                            st.dataframe(
                                locator_df,
                                width="stretch",
                            )

                    if mode == "По тегам":
                        if st.button("Собрать по тегам и сгенерировать локаторы"):
                            # Создаем прогресс-бар и контейнер для статуса
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            def update_progress(progress: float, message: str):
                                progress_bar.progress(progress)
                                status_text.text(message)
                            
                            try:
                                result = run_el_attr_workflow(
                                    target_url,
                                    selected_selectors or DEFAULT_SELECTORS,
                                    generate_selenide=generate_selenide,
                                    progress_callback=update_progress,
                                )
                                if isinstance(result, dict):
                                    locators = result.get("locators") or []
                                    selector_stats = result.get("selector_stats") or {}
                                else:
                                    locators = result or []
                                    selector_stats = {}

                                total_locators = len(locators)
                                valid_locators = sum(
                                    1 for item in (locators or []) if isinstance(item, dict) and item.get("exists")
                                )
                                
                                # Очищаем прогресс-бар и статус после завершения
                                progress_bar.empty()
                                status_text.empty()
                                
                                st.success("Готово.")
                                st.caption(
                                    f"Локаторов: **{total_locators}**, валидных: **{valid_locators}**."
                                )

                                st.session_state["el_attr_locators"] = locators or []
                                st.session_state["el_attr_selector_stats"] = selector_stats or {}
                            except Exception as e:
                                # Очищаем прогресс-бар и статус при ошибке
                                progress_bar.empty()
                                status_text.empty()
                                st.error(f"Ошибка при выполнении сценария: {e}")
                    else:
                        if st.button("Найти по описанию и сгенерировать локатор"):
                            if not prompt_description:
                                st.warning("Сначала введите описание элемента.")
                            else:
                                # Создаем прогресс-бар и контейнер для статуса
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                def update_progress(progress: float, message: str):
                                    progress_bar.progress(progress)
                                    status_text.text(message)
                                
                                try:
                                    result = run_el_attr_workflow(
                                        target_url,
                                        selectors=None,
                                        prompt_description=prompt_description,
                                        generate_selenide=generate_selenide,
                                        progress_callback=update_progress,
                                    )
                                    if isinstance(result, dict):
                                        locators = result.get("locators") or []
                                        selector_stats = result.get("selector_stats") or {}
                                    else:
                                        locators = result or []
                                        selector_stats = {}

                                    total_locators = len(locators)
                                    valid_locators = sum(
                                        1 for item in (locators or []) if isinstance(item, dict) and item.get("exists")
                                    )
                                    
                                    # Очищаем прогресс-бар и статус после завершения
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    st.success("Готово.")
                                    st.caption(
                                        f"Локаторов: **{total_locators}**, валидных: **{valid_locators}**."
                                    )
                                    if total_locators == 0:
                                        st.warning(
                                            "Не удалось найти элемент по описанию и сгенерировать локатор. "
                                            "Попробуйте ещё раз."
                                        )

                                    st.session_state["el_attr_locators"] = locators or []
                                    st.session_state["el_attr_selector_stats"] = selector_stats or {}
                                except Exception as e:
                                    # Очищаем прогресс-бар и статус при ошибке
                                    progress_bar.empty()
                                    status_text.empty()
                                    st.error(f"Ошибка при выполнении сценария: {e}")

                    saved_locators = st.session_state.get("el_attr_locators")
                    selector_stats = st.session_state.get("el_attr_selector_stats", {})

                    if selector_stats:
                        st.markdown("**Найденные элементы по выбранным селекторам:**")
                        for sel, count in selector_stats.items():
                            st.markdown(f"- `{sel}`: **{count}** элементов")

                    if saved_locators:
                        render_locator_panel(saved_locators)
                    elif saved_locators == []:
                        st.warning(
                            "Локаторы не были сгенерированы. "
                            "Попробуйте ещё раз."
                        )
