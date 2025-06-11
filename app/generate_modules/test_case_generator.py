from generate_modules.llama_index_integration import *
from src.utils import load_prompts
from streamlit_modules.session_manager import add_test_case
from src.logger import LOGGER
from src.text_constants import *
PROMPTS = load_prompts()

def choose_generate_response(**kwargs):

    LOGGER.info(LOGGER_INFO_START, choose_generate_response.__name__)
    if KEY_DESCRIPTION in kwargs:
        prompt_type = TYPE_PROMPT_WIKI
        LOGGER.info(LOGGER_INFO_START, prompt_type)

        if KEY_METHOD in kwargs and KEY_ENDPOINT in kwargs and KEY_BASE_URL in kwargs:
            prompt_type = kwargs[KEY_TYPE]
            LOGGER.info(LOGGER_INFO_START, prompt_type)
    else:
        return ST_WARNING_PLEASE_ENTER_DSCR

    # Получаем промпт из YAML
    prompt_template = PROMPTS.get(prompt_type, {}).get(KEY_CONTENT, KEY_EMPTY_KEY)
    if not prompt_template:
        return ERROR_PROMPT_NOT_FOUND

    # Формируем полный промпт
    existing_cases=kwargs.get(KEY_EXISTING_CASES, [])
    del kwargs[KEY_EXISTING_CASES]

    formatted_prompt = format_prompt(prompt_template, **kwargs)
    LOGGER.info(formatted_prompt)
    
    # Возвращаем результат
    if KEY_GENERATE_MORE in kwargs and kwargs[KEY_GENERATE_MORE]:
        new_cases = generate_test_cases_with_memory(
            prompt=formatted_prompt,
            count=kwargs.get(KEY_COUNT, 1),
            existing_cases=existing_cases#kwargs.get('existing_cases', [])
        )
        for case in new_cases:
            try:
                add_test_case(case)
            except Exception as e:
                return f"{ERROR_ADD_TEST_CASE} {str(e)}"
            
        return "\n\n".join(new_cases) 
    
    else:# len(kwargs.get('existing_cases', [])) == 0:
        # try:
        # Вызов метода complete
        llm = LocalLLM()
        new_cases = llm.complete(formatted_prompt)
        try:
            add_test_case(new_cases)
        except Exception as e:
            return  f"{ERROR_ADD_TEST_CASE} {str(e)}"
            
        LOGGER.info(LOGGER_INFO_END, choose_generate_response.__name__)
        # print(new_cases)
        return new_cases #{"text": new_cases}
        # except Exception as e:
        #     return {"error": f"Ошибка при генерации тестов: {str(e)}"}
    # else:
    #     LOGGER.info(LOGGER_INFO_END, choose_generate_response.__name__)
    #     return "" #{"text": ""}  # Не генерируем, если нет явного запроса


def format_prompt(prompt_template, **kwargs):
    """Формирует промпт на основе шаблона и переданных аргументов."""
    LOGGER.info(LOGGER_INFO_END, format_prompt.__name__)
    return prompt_template.format(**kwargs)
