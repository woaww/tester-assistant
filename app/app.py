import streamlit as st
from streamlit_modules.session_manager import (init_session)
from src.text_constants import AppSettings, APP_SIDE_PANEL_PARAMS
from src.models import ModelParamsConfig
from streamlit_modules.pages import auth_page, main_page
from src.mlflow_utilits import init_mlflow

# --- Инициализация ---
init_session()
init_mlflow()
model_params_config = ModelParamsConfig(**APP_SIDE_PANEL_PARAMS)

# Основная панель
st.set_page_config(page_title=AppSettings.PAGE_HOME, layout="centered")

page = st.query_params.get("page", ["auth_page"])[0]


if st.session_state["authenticated"]:
    # Если авторизован, показываем главную страницу
    main_page(model_params_config=model_params_config) # Замените model_params_config на ваш объект
else:
    # Если не авторизован, показываем страницу авторизации
    auth_page()