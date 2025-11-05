import streamlit as st
import os
from generate_modules.test_case_generator import (generate_api_test_cases, post_process_response,
                                                  generate_wiki_test_cases,
                                                  generate_jira_test_cases)
from src.specification_api import SpecificationParser
from streamlit_modules.session_manager import *
from src.text_constants import (Separatiors, AppSettings, UtilitsParsing, LoggerMsg,
                                LANGUAGE_MAPPING, LIKE, DISLIKE, STATS_EVAL_FILE)
from src.testit_client import TestItClient
from src.models import SectionCreateModel, ApiKwargs, WikiJiraKwargs
from src.utils import split_wiki_jira_tests_by_separator, ensure_stats_file
import pandas as pd
from typing import Optional, Callable
from src.jira_client import JiraClient
from src.wiki import WikiClient

def button_api_get_test_case(kwargs: ApiKwargs) -> None:
    match kwargs.type:
        case "api":
            try:
                parser = SpecificationParser(kwargs.spec_url)
                if parser.has_endpoint(kwargs.spec_path, kwargs.spec_method):
                    spec_description = parser.get_endpoint_spec(kwargs.spec_path, kwargs.spec_method)
                    with st.spinner(AppSettings.SPINNER):
                        response = generate_api_test_cases(
                            description=spec_description,
                            url_ref=kwargs.spec_url,
                            spec_method=kwargs.spec_method,
                            model_params=st.session_state.model_params
                        )
                        if kwargs.new_cases:
                            add_case(Separatiors.sep_cases + response, case_type=kwargs.type)
                        else:
                            st.session_state.api_cases = []
                            add_case(response, case_type=kwargs.type)

                        st.session_state.api_cases_generated = True
                        st.session_state.api_test_cases_response = response  # Сохраняем результат в session_state

                else:
                    st.session_state.api_error_message = "Введенного endpoint'а нет в спецификации"

            except Exception as e:
                st.session_state.api_error_message = f"Ошибка при обработке спецификации API: {e}"

        case "translate_test_cases":
            api_cases = get_api_cases()
            if not api_cases:
                st.session_state.api_error_message = "Сначала сгенерируйте тестовые кейсы в формате curl."
            else:
                with st.spinner(f"Преобразование тестовых кейсов на язык {kwargs.language}"):
                    response = generate_api_test_cases(
                        description="\n".join(api_cases),
                        url_ref=kwargs.spec_url,
                        model_params=st.session_state.model_params,
                        language=kwargs.language
                    )
                    st.session_state.translated_test_cases_response = post_process_response(response)

                    # Кнопка для скачивания
                    st.download_button(
                        label="Скачать результат",
                        data=st.session_state.translated_test_cases_response,
                        file_name=f"example.{LANGUAGE_MAPPING[kwargs.language].get('extension')}",
                        mime=LANGUAGE_MAPPING[kwargs.language]["mime"]
                    )

def button_jira_wiki_get_test_case(kwargs: WikiJiraKwargs) -> None:
    # if kwargs.description_text is None:
    #     st.session_state.jira_wiki_error_message = "Введите описание задачи"
    #     return

    match kwargs.source_type:
        case "wiki":
            if kwargs.new_cases and not get_wiki_cases_generated():
                st.session_state.jira_wiki_error_message = "Сначала сгенерируйте тест-кейсы!"
                return
            # if not kwargs.description_text:
            #     st.session_state.jira_wiki_error_message = "Введите URL страницы Wiki"
            #     return

            with st.spinner(AppSettings.SPINNER):
                response = generate_wiki_test_cases(
                    description=kwargs.description_text,
                    model_params=st.session_state.model_params
                )
                rep_w_separator = post_process_response(response)
                if kwargs.new_cases:
                    add_case(Separatiors.sep_cases + rep_w_separator, case_type=kwargs.source_type)
                else:
                    st.session_state.wiki_cases = []
                    add_case(rep_w_separator, case_type=kwargs.source_type)

                st.session_state.wiki_test_cases_response = split_wiki_jira_tests_by_separator(get_wiki_cases())

        case "jira":
            if kwargs.new_cases and not get_jira_cases_generated():
                st.session_state.jira_wiki_error_message = "Сначала сгенерируйте тест-кейсы!"
                return
            # if not kwargs.description_text:
            #     st.session_state.jira_wiki_error_message = "Введите URL страницы Jira"
            #     return

            with st.spinner(AppSettings.SPINNER):
                response = generate_jira_test_cases(
                    description=kwargs.description_text,
                    model_params=st.session_state.model_params
                )
                rep_w_separator = post_process_response(response)
                if kwargs.new_cases:
                    add_case(Separatiors.sep_cases + rep_w_separator, case_type=kwargs.source_type)
                else:
                    st.session_state.jira_cases = []
                    add_case(rep_w_separator, case_type=kwargs.source_type)

                st.session_state.jira_test_cases_response = split_wiki_jira_tests_by_separator(get_jira_cases())


def send_to_testit(new_section_name: str, 
                   source_type: str) -> None:
    """
    Отправляет тест-кейсы в TestIt из разных источников.

    Args:
        new_section_name: Название секции в TestIt.
        source_type: Источник тест-кейсов ("wiki" или "jira").
    """
    # Проверяем наличие тест-кейсов
    if source_type == "wiki" and not get_wiki_cases():
        st.warning("Нет тест-кейсов для отправки из Wiki. Сначала сгенерируйте кейсы.")
        return
    elif source_type == "jira" and not get_jira_cases():
        st.warning("Нет тест-кейсов для отправки из Jira. Сначала сгенерируйте кейсы.")
        return

    # Проверяем название секции
    if not new_section_name.strip():
        st.warning("Введите название секции для TestIt.")
        return

    # Получаем тест-кейсы в зависимости от источника
    if source_type == "wiki":
        test_cases = get_wiki_cases()
    elif source_type == "jira":
        test_cases = get_jira_cases()
    else:
        st.error(f"Неподдерживаемый источник тест-кейсов: {source_type}")
        return

    # Форматируем тест-кейсы
    full_test_cases = "\n\n---\n\n".join(
        str(case).replace(Separatiors.sep_cases, '') for case in test_cases if case.strip()
    )

    try:
        parsed_cases = TestItClient().parse_case(full_test_cases)
        total_cases = len(parsed_cases)

        if total_cases == 0:
            st.warning("⚠️ Не удалось распознать тест-кейсы. Проверьте формат.")
            st.text_input("Разобранный текст", full_test_cases)
            return

    except Exception as e:
        st.error(f"Ошибка при парсинге: {e}")
        return

    st.info(f"🚀 Начинаем загрузку {total_cases} тест-кейсов в TestIt...")

    try:
        client = TestItClient()
        new_section = client.create_section(SectionCreateModel(name=new_section_name.strip()))
        st.success(f"✅ Секция '{new_section_name.strip()}' создана")

    except Exception as e:
        st.error(f"❌ Ошибка при создании секции: {e}")
        return

    # Загрузка тест-кейсов с прогрессом
    progress_bar = st.progress(0)
    status_text = st.empty()
    success_count = 0
    failed_cases = []

    for i, case in enumerate(parsed_cases):
        try:
            case.project_id = UtilitsParsing.PROJECT_ID
            case.section_id = new_section
            client.create_testcase(case)
            success_count += 1

        except Exception as e:
            failed_cases.append(f"`{case.name}`: {e}")

        progress_bar.progress((i + 1) / total_cases)

    status_text.text("✅ Загрузка завершена")
    progress_bar.empty()

    if failed_cases:
        st.warning(f"✅ Успешно: {success_count}/{total_cases}")
        with st.expander("Показать ошибки"):
            for msg in failed_cases:
                st.markdown(f"- {msg}")
    else:
        st.success(f"✅ Все {total_cases} тест-кейсов успешно загружены в TestIt!")



def feedback_widget(
    df: pd.DataFrame,
    like_label: str = "👍 Нравится",
    dislike_label: str = "👎 Не нравится",
    on_like: Optional[Callable] = None,
    on_dislike: Optional[Callable] = None,
    key_prefix: str = "feedback"
) -> None:
    """
    Виджет для сбора фидбэка (лайк/дизлайк).

    :param df: DataFrame с данными, где нужно обновить рейтинг.
    :param like_label: Текст для кнопки "Лайк".
    :param dislike_label: Текст для кнопки "Дизлайк".
    :param on_like: Функция, вызываемая при нажатии на "Лайк".
    :param on_dislike: Функция, вызываемая при нажатии на "Дизлайк".
    :param key_prefix: Префикс для ключей кнопок.
    """
    col1, col2 = st.columns(2)

    with col1:
        st.button(
            like_label,
            key=f"{key_prefix}_like_{len(df) - 1}",
            on_click=on_like,
            args=(df,)
        )

    with col2:
        st.button(
            dislike_label,
            key=f"{key_prefix}_dislike_{len(df) - 1}",
            on_click=on_dislike,
            args=(df,)
        )


def update_rating(rating: str, df: pd.DataFrame) -> None:
    """Обновляет рейтинг в DataFrame и сохраняет в CSV."""
    df.loc[df.index[-1], "rating"] = rating
    df.to_csv(STATS_EVAL_FILE, index=False)
    st.success("Спасибо за ваш отзыв!")

def like_feedback(df: pd.DataFrame) -> None:
    """Обработчик нажатия на кнопку 'Лайк'."""
    update_rating(LIKE, df)

def dislike_feedback(df: pd.DataFrame) -> None:
    """Обработчик нажатия на кнопку 'Дизлайк'."""
    update_rating(DISLIKE, df)


def save_response_and_get_feedback(
    url: str,
    response: str, 
    path: str = None,
    method: str = None,
    # model_params: Optional[Dict[str, Union[float, int]]] = None,
) -> None:
    # Сохраняем ответ в DataFrame
    new_row = pd.DataFrame([{
        "url": url,
        "path": path,
        "method": method,
        "response": response,
        "rating": None,
    }])

    ensure_stats_file(STATS_EVAL_FILE)

    df = pd.read_csv(STATS_EVAL_FILE) if os.path.exists(STATS_EVAL_FILE) else pd.DataFrame(columns=['url','path','method','response','rating'])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    updated_df.to_csv(STATS_EVAL_FILE, index=False)

    # Отображаем виджет фидбэка
    st.write("Пожалуйста, оцените ответ:")
    feedback_widget(
        df=updated_df,
        on_like=like_feedback,
        on_dislike=dislike_feedback,
        key_prefix="response_feedback"
    )


def add_comment_to_issue(url: str, 
                         comment_body: str) -> dict:
    """
    Добавляет комментарий к задаче в Jira.

    :param ticket_id: Идентификатор задачи.
    :param comment_body: Текст комментария.
    :return: Информация о добавленном комментарии.
    """
    jc = JiraClient()
    try:
        ticket_id = jc.extract_ticket_id(url)
        issue = jc.jira.issue(ticket_id)
        comment = jc.jira.add_comment(issue, comment_body)
        return comment.raw
    except Exception as e:
        raise RuntimeError(f"{LoggerMsg.ERROR_JIRA_ADD_COMMENT}{str(e)}")
    

def add_comment_to_page(url: str, 
                        comment_body: str) -> dict:
    """
    Добавляет комментарий к странице Confluence.

    :param url: ID страницы, к которой нужно добавить комментарий.
    :param comment_body: Текст комментария.
    :param parent_id: ID родительского комментария (если комментарий является ответом на другой комментарий).
    :return: Информация о добавленном комментарии.
    """
    wc = WikiClient()

    separator = url.split('=', 1)
    page_id = separator[1] if len(separator) > 1 else url

    comment = wc.confluence.add_comment(
        page_id,
        comment_body
    )
    return comment