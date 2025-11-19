import streamlit as st
import mlflow
# from src.utils import generate_response

def init_session():
    if 'wiki_cases' not in st.session_state:
        st.session_state.wiki_cases = []

    if "wiki_cases_generated" not in st.session_state:
        st.session_state.wiki_cases_generated = False

    if 'api_cases' not in st.session_state:
        st.session_state.api_cases = []

    if "api_cases_generated" not in st.session_state:
        st.session_state.api_cases_generated = False

    if 'jira_cases' not in st.session_state:
        st.session_state.jira_cases = []

    if 'jira_cases_generated' not in st.session_state:
        st.session_state.jira_cases_generated = False

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = None



def get_wiki_cases():
    return st.session_state.wiki_cases

def get_api_cases():
    return st.session_state.api_cases

def get_jira_cases():
    return st.session_state.jira_cases

def get_wiki_cases_generated():
    return st.session_state.wiki_cases_generated

def get_api_cases_generated():
    return st.session_state.api_cases_generated

def get_jira_cases_generated():
    return st.session_state.jira_cases_generated

def add_case(new_case, case_type='wiki'):
    if case_type == 'wiki':
        st.session_state.wiki_cases.append(new_case)
        st.session_state.wiki_cases_generated = True
    elif case_type == 'api':
        st.session_state.api_cases.append(new_case)
        st.session_state.api_cases_generated = True
    elif case_type == 'jira':
        st.session_state.jira_cases.append(new_case)
        st.session_state.jira_cases_generated = True

def fn(new_case):
    if 'description' in new_case:
        return new_case['description']
    else:
        return new_case

def clear_session():
    st.session_state.wiki_cases = []
    st.session_state.api_cases = []
    st.session_state.jira_cases = []

def login_callback(email_value):
    if email_value:
        st.session_state["user_email"] = email_value
        st.session_state["authenticated"] = True
    else:
        st.error("Пожалуйста, введите email.")

def logout_callback():
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None