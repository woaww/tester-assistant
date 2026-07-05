import logging
import os

# Меньше «мусора» в консоли: предупреждения Streamlit (deprecation, accessibility) и INFO от browser_use.
# Для отладки UI: ST_VERBOSE_LOGS=1
if not os.getenv("ST_VERBOSE_LOGS", "").strip().lower() in ("1", "true", "yes"):
    logging.getLogger("streamlit").setLevel(logging.ERROR)
    logging.getLogger("browser_use").setLevel(logging.WARNING)

import streamlit as st

from streamlit_modules.dashboard_page import dashboard_page
from streamlit_modules.locators_page import locators_page
from streamlit_modules.pages import main_page
from streamlit_modules.projects_page import projects_page
from streamlit_modules.ui import init_session, render_param_slider, reset_params_to_default
from src.mlflow_utilits import init_mlflow
from src.models import ModelParamsConfig
from src.text_constants import APP_SIDE_PANEL_PARAMS

st.set_page_config(page_title="LocatorAI", page_icon="🎯", layout="centered", initial_sidebar_state="expanded")

init_session()
init_mlflow()
model_params_config = ModelParamsConfig(**APP_SIDE_PANEL_PARAMS)

with st.sidebar:
    st.markdown("### Параметры")
    st.caption("LLM")
    if "model_params" not in st.session_state:
        st.session_state.model_params = reset_params_to_default(model_params_config)
    params_dict = {}
    for param_name, param_data in model_params_config.__dict__.items():
        params_dict[param_name] = render_param_slider(param_data, f"param_{param_name}")
    st.session_state.model_params.update(params_dict)
    st.divider()
    st.caption("Генерация")
    st.number_input("Chunk size", min_value=1, max_value=50, value=6, step=1, key="el_attr_chunk_size")
    st.number_input("Chunk size (fix)", min_value=1, max_value=50, value=5, step=1, key="el_attr_fix_chunk_size")
    st.number_input("Макс. элементов", min_value=1, max_value=1000, value=400, step=50, key="el_attr_max_total_elements")
    st.number_input("Макс. дочерних", min_value=1, max_value=2000, value=400, step=50, key="el_attr_max_children_elements")

st.markdown("## 🎯 LocatorAI")

tab_gen, tab_proj, tab_loc, tab_dash = st.tabs(["Генератор", "Проекты", "Локаторы", "Dashboard"])

with tab_gen:
    main_page()
with tab_proj:
    projects_page()
with tab_loc:
    locators_page()
with tab_dash:
    dashboard_page()
