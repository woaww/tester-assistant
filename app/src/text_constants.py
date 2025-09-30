from dotenv import load_dotenv
import os

load_dotenv()

LIKE = "like"
DISLIKE = "dislike"
STATS_EVAL_FILE = os.path.join(os.getcwd(),"data","tester-assistant-stats","stats_eval.csv") 

LLM_URL = os.getenv("LLM_URL")
WIKI_TOKEN = os.getenv("WIKI_TOKEN")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
TESTIT_TOKEN =  os.getenv("TESTIT_TOKEN")


PART_PAGE_PREDUSLOVIE = "Предусловия"
PART_PAGE_MAIN_USLOVIE = "Основной сценарий"
PART_PAGE_ALT_USLOVIE = "Альтернативный сценарий"
PART_PAGE_SCENARIO = "Сценарий"
PART_PAGE_POSTUSLOVIE = "Постусловия"

SELECTOR_STR_PREDUSLOVIE = f'th:-soup-contains("{PART_PAGE_PREDUSLOVIE}") + td'
SELECTOR_STR_MAIN_USLOVIE = f'th:-soup-contains("{PART_PAGE_MAIN_USLOVIE}") + td'
SELECTOR_STR_ALT_USLOVIE = f'th:-soup-contains("{PART_PAGE_ALT_USLOVIE}") + td'
SELECTOR_STR_SCENARIO = f'th:-soup-contains("{PART_PAGE_SCENARIO}") + td'
SELECTOR_STR_POSTUSLOVIE = f'th:-soup-contains("{PART_PAGE_POSTUSLOVIE}") + td'

LANGUAGE_MAPPING = {
    "Python": {
        "extension": "py",
        "mime": "text/x-python"
    },
    "Java": {
        "extension": "java",
        "mime": "text/x-java-source"
    }
    # Можно добавить другие языки по аналогии
}

class Separatiors:
    sep_cases: str = '✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱✱'

class Keys:
    GENERATED_TEXT: str = "generated_text"
    SPACE: str = " "
    EMPTY: str = ""
    SPLIT_SIGN: str = ","
    CONTENT: str = "content"
    TITLE: str = "title"

class UtilitsParsing:
    #Используется для создаиния конфлю-эклиента
    URL_WIKI: str = "https://wiki.domrf.ru"
    URL_JIRA: str = "https://jira.domrf.ru"
    URL_TESTIT: str = 'https://testit.domrf.ru'
    SECTION_TESTIT: str = "4d3811ab-7b03-4b76-9685-68c69d973e68"
    PROJECT_ID: str = "94983664-636a-4f9c-90e7-07f768df7979"
    #Используется для извлечения ID страницы из URL
    PATTERN_URL_ID: str = r'pageId=(\d+)'
    NOT_HEADERS_TIM = "ТИМ"
    NOT_HEADERS_US = "US"
    SELECTOR_PREDUSLOVIE = 'th:-soup-contains("Предусловия") + td'
    SELECTOR_MAIN_USLOVIE = 'th:-soup-contains("Основной сценарий") + td'
    SELECTOR_ALT_USLOVIE = 'th:-soup-contains("Альтернативный сценарий") + td'
    SELECTOR_SCENARIO = 'th:-soup-contains("Сценарий") + td'
    SELECTOR_POSTUSLOVIE = 'th:-soup-contains("Постусловия") + td'
    PATTERN_CLEAN: str = r'[^a-zA-Z\s-]'
    PATTERN_CLEAN_SPACE: str = r'\s+'
    PATTERN_URL: str = r'^(http|https)://'

#TODO:вынести паттерны в отдельный класс

class DefaultValuesLLM:
    DEF_TEMPERATURE: float = 0.15
    DEF_MAX_NEW_TOKENS: int = 2500
    DEF_REPETITION_PENALTY: float = 1.2
    DEF_FREQUENCY_PENALTY: float = 0.9

class AppSettings:
    EXPANDER: str = "ℹ️ Подробнее"
    HEADER_SETTINGS: str = "Настройки"
    PAGE_HOME = "Генератор тест-кейсов"
    ST_SELECTBOX = "Выберите тип генерации"
    BUTTON_RESET = "Сбросить параметры"
    BUTTON_GET_CASES = "Получить тест-кейсы"
    BUTTON_GET_MORE_CASES = "Сгенерировать ещё"
    SPINNER = "Генерация тест-кейсов..."
    SESSION_STATE_TEST_CASES = "test_cases"
    SESSION_STATE_EXISTING_CASES = "existing_cases"
    DSCR_BASE_URL_VALUE = "https://api.example.com"
    DSCR_BASE_PATH_VALUE = "/path"
    DSCR_BASE_METHOD_VALUE = "get"
    TYPE_OPTION_WIKI = "Генерация тестового кейса из сценария задачи (Вики)"
    TYPE_OPTION_CURL = "Генерация тестовых кейсов API (CURL)"
    TYPE_OPTION_JIRA = "Генерация тестового кейса из сценария задачи (Jira)"
    OPTIONS_LIST = [TYPE_OPTION_WIKI, TYPE_OPTION_CURL, TYPE_OPTION_JIRA]

class GeneralUtilitsConsts:
    #Тип кодировки - prompts
    TYPE_ENCODING: str = "utf-8"
    #Заголовки запроса к LLM
    HEADERS: dict = {"Content-Type": "application/json",
                        'accept': 'application/json',}
    RETRY_TRIES: int = 8
    MODEL_LOCAL_NAME: str = "local-model"


class LoggerMsg:
    ERROR_WIKI_GET_SCENARIO = "Ошибка получения сценария: " #!!!
        #Шаблон сообщения об ошибке
    ERROR: str = "An error"
    #Информационное сообщение о получении обратной связи
    INFO_GET_FEEDBACK: str = "Get feedback"
    #о записи обратной связи
    INFO_WRITE_FEEDBACK: str = "Writing feedback"
    #о начале операции
    INFO_START: str = "Starting"
    #о завершении операции
    INFO_END: str = "Completed"
      #сообщение о ответе модели
    INFO_LLM_RESPONSE: str = "LLM Response: %s, Заголовок блока: %s"
    #сообщение о промпте
    INFO_PROMPT: str = "Prompt: %s, Заголовок блока: %s"
    #сообщение о результате до обновления
    ERROR_GET_DATA_PAGE: str = "Ошибка получения данных страницы: "
    ERROR_EXTRACT_LINK_WIKI: str = "Пожалуйста, введите корректную ссылку (должна начинаться с http:// или https://)."
    ERROR_JIRA_GET_SUMMARY: str = "Ошибка получения заголовка тикета: "
    ERROR_JIRA_GET_DESCRIPTION: str = "Ошибка получения описания тикета: "

    SPEC_API_READ_ERROR = "Ошибка чтении спецификации"
    SPEC_API_PARSE_ERROR = "Ошибка при парсинге спецификации"
    SPEC_API_PARSE_ERROR_EMPTY = "Спецификация загружена, но оказалась пустой после парсинга."


class GeneralValuesLLM:
    GEN_RESPONSE_TEMP: float = 0.15
    GEN_RESPONSE_MAX_TOKENS: int = 1000
    GEN_RESPONSE_REPETITION_PENALTY: float = 1.2
    GEN_RESPONSE_FREQUENCY_PENALTY: float = 0.4
    GEN_RESPONSE_TOP_K: int = 60
    GEN_RESPONSE_TOP_N_TOKENS: int = 5
    GEN_RESPONSE_TOP_P: float = 0.8

DefaultValuesLLM = DefaultValuesLLM()

APP_SIDE_PANEL_PARAMS = {
    "temperature": {
        "label": "Температура: {}",
        "description": (
            "Температура (0.0 - 1.0):\n"
            "- Низкая (ближе к 0) = более предсказуемые ответы\n"
            "- Высокая (ближе к 1) = более креативные, разнообразные, но рискованные ответы\n"
            "- Представьте как регулятор творческой свободы модели"
        ),
        "select": "Задать температуру LLM",
        "options": {
            "start": 0.0,
            "stop": 1.0,
            "step": 0.05,
            "decimals": 2
        },
        "default": DefaultValuesLLM.DEF_TEMPERATURE
    },
    "max_new_tokens": {
        "label": "Максимальное количество новых токенов: {}",
        "description": (
            "Максимальное количество токенов:\n"\
            "- Ограничивает длину ответа\n"\
            "- Один токен ≈ 4 символа или часть слова\n"\
            "- Чем больше токенов, тем длиннее может быть ответ"
        ),
        "select": "Задать максимальное количество токенов",
        "options": {
            "start": 1,
            "stop": DefaultValuesLLM.DEF_MAX_NEW_TOKENS+1001,
            "step": 1,
            "decimals": 0
        },
        "default": DefaultValuesLLM.DEF_MAX_NEW_TOKENS
    },
    "repetition_penalty": {
        "label": "Штраф за повторение: {}",
        "description": (
            "Repetition Penalty (штраф за повторения):\n"\
            "- Предотвращает повторение одних и тех же фраз\n"\
            "- Высокое значение = модель старается избегать повторений\n"\
            "- Низкое значение = возможны повторы"
        ),
        "select": "Задать штраф за повторение",
        "options": {
            "start": 1.0,
            "stop": 3.0,
            "step": 0.1,
            "decimals": 1
        },
        "default": DefaultValuesLLM.DEF_REPETITION_PENALTY
    },
    "frequency_penalty": {
        "label": "Штраф за частоту: {}",
        "description": (
            "Frequency Penalty (штраф за частоту):\n"\
            "- Снижает вероятность использования часто встречающихся слов\n"\
            "- Высокое значение = более редкие и уникальные слова\n"\
            "- Низкое значение = более знакомые слова и фразы"

        ),
        "select": "Задать штраф за частоту",
        "options": {
            "start": 0.0,
            "stop": 1.0,
            "step": 0.1,
            "decimals": 1
        },
        "default": DefaultValuesLLM.DEF_FREQUENCY_PENALTY
    }
}
