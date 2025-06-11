import streamlit as st
from streamlit_modules.session_manager import *
from src.text_constants import *
from src.models import *

def display_delete_tokens(wiki=True):
    st.subheader(ST_REMOVED_TOKENS)
    
    if wiki:
        if st.button(ST_WIKI_TOKEN_REMOVED_QA):
            if not validate_wiki_token():
                st.stop()
            delete_tokens(wiki_token=st.session_state.wiki_token)
            st.success(ST_WIKI_TOKEN_REMOVED)
    else:
        if st.button(ST_JIRA_TOKEN_REMOVED_QA):
            if not validate_jira_token():
                st.stop()
            delete_tokens(jira_token=st.session_state.jira_token)
            st.success(ST_JIRA_TOKEN_REMOVED)

def display_input_tokens(wiki=True):
    """
    Displays input fields for Jira and Wiki tokens and a button to save them.

    Prompts the user to input Jira and Wiki tokens using password-protected text
    input fields. When the "Сохранить токены" button is pressed, the tokens are
    saved to the session state, and a success message is displayed.
    """

    st.subheader(INPUT_TOKENS)
    if wiki:
        st.write(ST_WARNING_MSG_WIKI)
        wiki_token_input = st.text_input(WIKI_TOKEN_NAME, 
                                         type=TYPE_TOKENS, 
                                         key="wiki_token_input")
        if st.button(ST_TOKEN_SAVED_QA):
            st.session_state.wiki_token = wiki_token_input
            st.success(ST_TOKEN_SAVED)
    else:
        st.write(ST_WARNING_MSG_JIRA)    
        jira_token_input = st.text_input(JIRA_TOKEN_NAME, 
                                         type=TYPE_TOKENS, 
                                         key="jira_token_input")
        if st.button(ST_TOKEN_SAVED_QA):
            st.session_state.jira_token = jira_token_input
            st.success(ST_TOKEN_SAVED)


def render_param_slider(param_data: AppSettingsParamConfig):
    """
    Renders a Streamlit slider for a given parameter.

    :param param_data: The configuration for the parameter to render.
    :return: The rendered slider.
    """
    st.markdown(SEPARATION_STR)
    st.caption(param_data.label)
    with st.expander(EXPANDER):
        st.caption(param_data.description)
    return st.select_slider(
        label=param_data.select,
        options=param_data.options,
        value=param_data.default,
        key=param_data.select
    )
