import streamlit as st
from src.utils import generate_response

def init_session():
    if 'wiki_cases' not in st.session_state:
        st.session_state.wiki_cases = []

    if "wiki_cases_generated" not in st.session_state:
        st.session_state.wiki_cases_generated = False

    if 'api_cases' not in st.session_state:
        st.session_state.api_cases = []

    if "api_cases_generated" not in st.session_state:
        st.session_state.api_cases_generated = False

def get_wiki_cases():
    return st.session_state.wiki_cases

def get_api_cases():
    return st.session_state.api_cases

def add_case(new_case, case_type='wiki'):
    if case_type == 'wiki':
        st.session_state.wiki_cases.append(new_case)
    else:
        st.session_state.api_cases.append(new_case)

def fn(new_case):
        if 'description' in new_case:
            return new_case['description']
        else:
            return new_case

def is_unique(new_case, case_type='wiki'):

    # Получаем список тест-кейсов по типу
    cases = get_wiki_cases() if case_type == 'wiki' else get_api_cases()

    # Если список пуст — уникальный
    if not cases:
        return True

    # Собрать историю тест-кейсов
    history = "\n".join([f"- {case['id']}: {case['description']}" for case in cases])

    # Формируем промпт для LLM
    prompt = f"""
    Пожалуйста, проанализируй следующий тест-кейс и определи, является ли он дубликатом по смыслу среди уже существующих.

    Новый тест-кейс:
    {fn(new_case)}

    Список уже существующих тест-кейсов:
    {history}

    Ответ:
    - "Дубликат" если по смыслу повторяет один из уже существующих.
    - "Уникальный" если не повторяет.

    Также верни **вероятность** (от 0 до 1), с которой этот тест-кейс может быть дубликатом.

    Формат ответа:
    [Тип] [Вероятность]
    Пример:
    Дубликат 0.85
    Уникальный 0.15
    """

    # Вызов твоей локальной модели (LocalLLM)
    response = generate_response(prompt)

    # Логирование
    st.write(f"LLM Response: {response}")

    # Парсим ответ
    try:
        parts = response.strip().split()
        case_type = parts[0]
        probability = float(parts[1])
        return case_type == "Уникальный"
    except Exception as e:
        st.warning(f"Ошибка при парсинге ответа модели: {e}")
        return False

def clear_session():
    st.session_state.wiki_cases = []
    st.session_state.api_cases = []