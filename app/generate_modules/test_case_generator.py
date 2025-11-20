from src.logger import log_function_call
from src.text_constants import Keys
from src.utils import load_prompts
from src.utils import sync_generate_response
from streamlit_modules.session_manager import get_wiki_cases, get_api_cases, get_jira_cases
import re 

PROMPTS = load_prompts()

@log_function_call()
def format_prompt(prompt_template, **kwargs):
    """Формирует промпт на основе шаблона и переданных аргументов."""
    return prompt_template.format(**kwargs)

@log_function_call()
def post_process_response(response: str) -> str:
    # Удаление блоков <think>...<think> (включая пустые)
    cleaned_text = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    cleaned_text = re.sub(r'</?think>', '', cleaned_text)  # Удаление одиночных тегов <think> или </think>

    # Удаление тегов </no> и любых других <no> тегов
    cleaned_text = re.sub(r'</?no>', '', cleaned_text)

    # Удаление специальных маркеров вроде <|End of user message|>
    cleaned_text = re.sub(r'<\|[^|]*\|>', '', cleaned_text)

    # Удаление упоминаний "Assistant:" и подобных
    cleaned_text = re.sub(r'^(Assistant\s*:|Bot\s*:)\s*', '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'\b(Assistant|Bot):?', '', cleaned_text, flags=re.IGNORECASE)

    # Удаление множественных пробелов и переносов строк, нормализация пробелов
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    return cleaned_text

@log_function_call() #TODO: исправить логирование ---> prompt [:10]
def generate_wiki_test_cases(description: str,
                             model_params) -> str:

    
    prompt_template = PROMPTS.get("test_case_prompt", {}).get(
        Keys.CONTENT, Keys.EMPTY)
    # system_prompt = PROMPTS.get("system_prompt_wiki_jira", {}).get(Keys.CONTENT, Keys.EMPTY)
    formatted_prompt = format_prompt(prompt_template=prompt_template,
                                     existing_cases= get_wiki_cases(),
                                     description=description)
    response = sync_generate_response(prompt_input=formatted_prompt,
                                    #   system_prompt=system_prompt,
                                        model_params=model_params)

    return response

@log_function_call()
def generate_api_test_cases(description: str,
                            url_ref: str,
                            model_params,
                            spec_method: str = None,
                            language: str = None) -> str:
    if language is None or language.lower() == "curl":
        prompt_template = PROMPTS.get("api_curl_test_case_prompt", {}).get(
            Keys.CONTENT, Keys.EMPTY)
        # system_prompt = PROMPTS.get("system_prompt_api", {}).get(Keys.CONTENT, Keys.EMPTY)
        formatted_prompt = format_prompt(prompt_template=prompt_template,
                                         url_ref=url_ref,
                                         method=spec_method,
                                         existing_cases=get_api_cases(),
                                         description=description)
    else:
        prompt_template = PROMPTS.get("api_languages_test_case_prompt", {
        }).get(Keys.CONTENT, Keys.EMPTY)
        # system_prompt = PROMPTS.get("system_prompt_api_translate", {}).get(Keys.CONTENT, Keys.EMPTY)
        formatted_prompt = format_prompt(prompt_template=prompt_template,
                                         description=description,
                                         language=language)

    response = sync_generate_response(prompt_input=formatted_prompt,
                                    #   system_prompt=system_prompt,
                                    model_params=model_params)

    return response

@log_function_call()
def generate_jira_test_cases(description: str,
                             model_params) -> str:

    prompt_template = PROMPTS.get("test_case_prompt", {}).get(
        Keys.CONTENT, Keys.EMPTY)
    # system_prompt = PROMPTS.get("system_prompt_wiki_jira", {}).get(Keys.CONTENT, Keys.EMPTY)
    formatted_prompt = format_prompt(prompt_template=prompt_template,
                                     existing_cases=get_jira_cases(),
                                     description=description)

    response = sync_generate_response(prompt_input=formatted_prompt,
                                    #   system_prompt=system_prompt,
                                 model_params=model_params)

    return response
