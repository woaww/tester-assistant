from src.logger import LOGGER
from src.text_constants import LoggerMsg, PostProcStr
from src.text_constants import KEY_CONTENT, KEY_EMPTY_KEY
from src.utils import load_prompts
from src.utils import generate_response

PROMPTS = load_prompts()

def format_prompt(prompt_template, **kwargs):
    """Формирует промпт на основе шаблона и переданных аргументов."""
    LOGGER.info(LoggerMsg.INFO_END, format_prompt.__name__,'')
    return prompt_template.format(**kwargs)

def post_process_response(response: str) -> str:
    LOGGER.info(LoggerMsg.INFO_START, post_process_response.__name__,'')
    
    for el in PostProcStr.LIST_DEL_STR:
        response = response.replace(el, '')

    LOGGER.info(LoggerMsg.INFO_END, post_process_response.__name__,'')
    return response

def generate_wiki_test_cases(description: str, 
                             model_params) -> str:
    
    LOGGER.info(LoggerMsg.INFO_START, generate_wiki_test_cases.__name__,'')

    prompt_template = PROMPTS.get("test_case_prompt", {}).get(KEY_CONTENT, KEY_EMPTY_KEY)
    formatted_prompt = format_prompt(prompt_template=prompt_template,
                                    description=description)
    print(formatted_prompt)
    response = generate_response(prompt_input=formatted_prompt, 
                            model_params=model_params)

    LOGGER.info(LoggerMsg.INFO_END, generate_wiki_test_cases.__name__,'')

    return response

def generate_api_test_cases(description: str, 
                            url_ref: str,
                            model_params, 
                            spec_method: str = None,
                            language: str = None) -> str:
   
    LOGGER.info(LoggerMsg.INFO_START, generate_api_test_cases.__name__,'')

    if language is None or language.lower() == "curl":
        prompt_template = PROMPTS.get("api_curl_test_case_prompt", {}).get(KEY_CONTENT, KEY_EMPTY_KEY)
        formatted_prompt = format_prompt(prompt_template=prompt_template,
                                        url_ref=url_ref,
                                        method=spec_method,
                                        description=description)
    else:
        prompt_template = PROMPTS.get("api_languages_test_case_prompt", {}).get(KEY_CONTENT, KEY_EMPTY_KEY)
        formatted_prompt = format_prompt(prompt_template=prompt_template,
                                        description=description,
                                        language=language)
    
    response = generate_response(prompt_input=formatted_prompt, 
                            model_params=model_params)

    LOGGER.info(LoggerMsg.INFO_END, generate_api_test_cases.__name__,'')

    return response