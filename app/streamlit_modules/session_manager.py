from src.logger import LOGGER
from src.text_constants import *
import streamlit as st
def init_session_state():
    LOGGER.info(LOGGER_INFO_START, init_session_state.__name__)
    if SESSION_STATE_JIRA_TOKEN not in st.session_state:
        st.session_state.jira_token = ""
    if SESSION_STATE_WIKI_TOKEN not in st.session_state:
        st.session_state.wiki_token = ""
    if SESSION_STATE_TEST_CASES not in st.session_state:
        st.session_state.test_cases = []
    if SESSION_STATE_EXISTING_CASES not in st.session_state:
        st.session_state.existing_cases = []
    LOGGER.info(LOGGER_INFO_END, init_session_state.__name__)

def get_test_cases():
    """Возвращает уже сгенерированные тест-кейсы."""
    LOGGER.info(LOGGER_INFO_START, get_test_cases.__name__)
    if SESSION_STATE_TEST_CASES not in st.session_state:
        st.session_state.test_cases = []
    LOGGER.info(LOGGER_INFO_END, get_test_cases.__name__)
    return st.session_state.test_cases

def add_test_case(case):
    """
    Добавляет новый тест-кейс в session_state.
    
    :param case: Строка с тест-кейсом
    """
    # init_session_state()
    LOGGER.info(LOGGER_INFO_START, add_test_case.__name__)
    if not case:
        LOGGER.warning(LOGGER_WARNING_EMPTY_CASE) 
        return
    
    # Добавляем кейс в session_state.test_cases
    st.session_state.test_cases.append(case)
    
    # Добавляем кейс в session_state.existing_cases
    st.session_state.existing_cases.append(case)
    LOGGER.info(LOGGER_INFO_END, add_test_case.__name__)

def delete_tokens(jira_token=None, wiki_token=None):
    """
    Удаляет токены из сессии.
    
    :param jira_token: Токен Jira (необязательный)
    :param wiki_token: Токен Wiki (необязательный)
    """
    LOGGER.info(LOGGER_INFO_START, delete_tokens.__name__)
    if jira_token is None:
        st.session_state.jira_token = KEY_EMPTY_KEY
    else:
        if st.session_state.jira_token == jira_token:
            st.session_state.jira_token = KEY_EMPTY_KEY

    if wiki_token is None:
        st.session_state.wiki_token = KEY_EMPTY_KEY
    else:
        if st.session_state.wiki_token == wiki_token:
            st.session_state.wiki_token = KEY_EMPTY_KEY

    LOGGER.info(LOGGER_INFO_END, delete_tokens.__name__)


def check_tokens(jira_token: str, wiki_token: str) -> bool:
    """
    Проверяет, введены ли токены.
    
    :param jira_token: Токен Jira
    :param wiki_token: Токен Wiki
    :return: True, если хотя бы один токен введён, иначе False
    """
    LOGGER.info(LOGGER_INFO_START, check_tokens.__name__)
    if not jira_token and not wiki_token:
        LOGGER.info(LOGGER_INFO_END, check_tokens.__name__)
        return False
    LOGGER.info(LOGGER_INFO_END, check_tokens.__name__)
    return True

def check_jira_token(jira_token: str) -> bool:
    """Проверяет, введён ли Jira-токен."""
    return bool(jira_token)

def check_wiki_token(wiki_token: str) -> bool:
    """Проверяет, введён ли Wiki-токен."""
    return bool(wiki_token)


# Функция для проверки наличия токенов
def validate_tokens():
    if not check_tokens(st.session_state.jira_token, st.session_state.wiki_token):
        st.warning(ST_WARNING_TOKEN)
        return False
    return True

# Функция для проверки Jira-токена
def validate_jira_token():
    if not check_jira_token(st.session_state.jira_token):
        st.warning(ST_WARNING_TOKEN_JIRA)
        return False
    return True

# Функция для проверки Wiki-токена
def validate_wiki_token():
    if not check_wiki_token(st.session_state.wiki_token):
        st.warning(ST_WARNING_TOKEN_WIKI)
        return False
    return True