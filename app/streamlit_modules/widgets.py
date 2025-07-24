import streamlit as st
from app.src.logger import LOGGER
from src.text_constants import LoggerMsg, Separatiors
from generate_modules.test_case_generator import generate_api_test_cases
from src.specification_api import SpecificationParser
from streamlit_modules.session_manager import add_case
from src.text_constants import AppSettings
from streamlit_modules.settings import is_api_url_method

def button_get_test_case(spec_url: str,
                         spec_method: str,
                         type: str,
                         new_cases: bool) -> str:

    match type:
        case "api":
            
            st.session_state.api_cases = []

            if not spec_url:
                st.warning("Введите URL спецификации API")
                return
            else:
                try:
                    res_url_method = is_api_url_method(spec_url, spec_method)
                    parser = SpecificationParser(res_url_method["url"])
                    spec_description = parser.parse_specification(res_url_method["method"])
                    
                    with st.spinner(AppSettings.SPINNER):
                        response = generate_api_test_cases(
                            description=spec_description,
                            url_ref = res_url_method["url"],
                            spec_method=res_url_method["method"],
                            model_params=st.session_state.model_params
                        )
                        if new_cases:
                            add_case(Separatiors.sep_cases+response,
                                     case_type='api')
                        else:
                            add_case(response, case_type='api')
                            
                        st.session_state.api_cases_generated = True

                except Exception as e:
                    st.error(f"Ошибка при обработке спецификации API")
                    LOGGER.error(LoggerMsg.ERROR_GENERATE_API_TEST_CASES,
                                 SpecificationParser.__name__, e)