from dotenv import load_dotenv
import os

load_dotenv()

LLM_URL = os.getenv("LLM_URL")
WIKI_TOKEN = os.getenv("WIKI_TOKEN")
# Logger constatns

LOG_FORMAT = ('%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] '
              '%(message)s - Function: %(funcName)s')
LOG_DATETIME_FORMAT = '%Y-%m-%d:%H:%M:%S'

# Константны для display settings



SEPARATION_STR  = "---"


HEADER_SETTINGS = "Настройки"
CURRENT_GENERATION_PARAMETERS = "Текущие параметры генерации:"
CHOOSE_PROMPT = "Задайте промпт:"
YOUR_CHOOSE = "Вы выбрали:"


#Ролевые константы

ROLE_ASSISTANT = "assistant"
ROLE_USER = "user"
CONTENT = "content"
# MESSAGE = "messages"

# Константы для записи в файл для сборки статистики
# COLUMN_EMAIL = "email"
# COLUMN_PROMPT = "prompt"
# COLUMN_FILE = "file"
PARAMETR_TEMPERATURE = "temperature"
PARAMETR_MAX_NEW_TOKENS = "max_new_tokens"
PARAMETR_REPETITION_PENALTY = "repetition_penalty"
PARAMETR_FREQUENCY_PENALTY = "frequency_penalty"
COLUMN_RESPONSE_EVAL = "response_eval"
COLUMN_RATING = "rating"
COLUMN_FEEDBACK_TEXT = "feedback_text"

# LIST_OF_COLUMNS_STATS_FILE = [
#     "email", "model", "file", "version_prompt",
#     "temperature", "max_new_tokens",
#     "repetition_penalty", "frequency_penalty",
#     "response_eval", "rating", "feedback_text"
# ]


# Паттерн для обработки строки

URL_WIKI = 'https://wiki.domrf.ru'
PATTERN_URL_IN_HTTP = 'http'
# PATTERN_URL = r'^(http|https)://'
PATTER_PAGE_ID = r'pageId=(\d+)'
# PATTER_EVAL = r"### Оценка:\s*(\d+)"
# PATTERN_CLEAN = r'[^a-zA-Z\s-]'
# PATTERN_CLEAN_SPACE = r'\s+'
KEY_FOR_SPACE = " "
KEY_EMPTY_KEY = ''

# Константы эмодзи
# Для оценок добавляем форму с обратной связью от пользователь
LIKE = "👍"
DCRPTN_LIKE = "Полезный ответ"
TNK_EVAL = "Спасибо за оценку и обратную связь!"
DISLIKE = "👎" 
DCRPTN_DISLIKE = "Не очень"
DEFAULT_RATING_EMOJI = {"like": LIKE, "dislike": DISLIKE}
EVAL_AMZ = "🔥"
EVAL_OK = "👌"
EVAL_SAD = "😔"

HEADERS = {
    "Content-Type": "application/json", 
    'accept': 'application/json', }

TYPE_ENCODING = 'utf-8'
SPLIT_SIGN = ","

# LOGGER messagess

LOGGER_ERROR = "An error %s in %s" #!!!

LOGGER_WARNING_EMPTY_CASE = "Попытка добавить пустой тест-кейс."
# LOGGER_INFO_WRITE_FEEDBACK = "Writing feedback"
LOGGER_INFO_START = "Starting %s" #!!!
LOGGER_INFO_END = "Completed %s" #!!!


# KEYS from dictionaries

KEY_RESULT = "result"
KEY_TEXT = "text"
KEY_PROMPT = "prompt"
KEY_TEMPLATE = "template"
KEY_TEMPLATE_TEXT = "template_text"
KEY_INPUT_VARIABLES = "input_variables"
KEY_CONTENT = "content"
KEY_TITLE = "title" #!!!

KEY_STATUS_FOR_USECASE = 'status_for_usecase'
KEY_GENERATED_TEXT = 'generated_text'
KEY_RESPONSE_EVAL = 'response_eval'
KEY_RATING = 'rating'
KEY_ROLE = "role"
KEY_ROLES = "roles"
KEY_DISLIKE = "dislike"
KEY_LIKE = "like"

KEY_COUNT = "count"
KEY_EXISTING_CASES = "existing_cases"
KEY_METHOD = "method"
KEY_DESCRIPTION = "description"
KEY_ENDPOINT = "endpoint"
KEY_BASE_URL = "base_url"
KEY_GENERATE_MORE = "generate_more"
KEY_TYPE = "type"


# constatns for formatted data



NOT_HEADERS_TIM = "ТИМ"
NOT_HEADERS_US = "US"

ST_WARNING_TOKEN = "Пожалуйста, введите хотя бы один токен."
ST_WARNING_TOKEN_WIKI = "Пожалуйста, введите Wiki-токен."
ST_WARNING_TOKEN_JIRA = "Пожалуйста, введите Jira-токен."

# можно добаавить проверку на адрес для яндекса
EXPANDER = "ℹ️ Подробнее"

FEEDBACK_STATS = "### 📊 Статистика оценок"
ALL_EVALUATION = "**Всего оценок:**"
NEGATIVE_EVALUATION = "**Отрицательных:**"
POSITIVE_EVALUATION = "**Положительных:**"
INFO_EVALUATION = "Нет данных для отображения."

SESSION_STATE_JIRA_TOKEN = "jira_token"
SESSION_STATE_WIKI_TOKEN = "wiki_token"
SESSION_STATE_TEST_CASES = "test_cases"
SESSION_STATE_EXISTING_CASES = "existing_cases"


ST_SELECTBOX = "Выберите действие"

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

LANGUAGE_BASH = "bash"
LANGUAGE_JAVA = "java"
LANGUAGE_PYTHON = "python"
LANGUAGE_CURL = "CURL"

ST_WARNING_PLEASE_ENTER = "Пожалуйста, введите метод и endpoint."
ST_WARNING_PLEASE_ENTER_DSCR = "Пожалуйста, введите описание задачи."
ST_INFO_WORK = "Перед работой обязательно введите токен, если будете отправлять ссылку на Вики."
ST_INFO_ENTER_TEXT_LINK = "Введите ссылку/тект задачи."

BUTTON_GET_CASES = "Сгенерировать кейсы"
BUTTON_GET_MORE_CASES = "Сгенерировать ещё кейсы"

BUTTON_GET_CASES_PYTHON = f"{BUTTON_GET_CASES} {LANGUAGE_PYTHON} тесты"
BUTTON_GET_MORE_CASES_PYTHON = f"{BUTTON_GET_MORE_CASES} {LANGUAGE_PYTHON} тесты"

BUTTON_GET_CASES_JAVA = f"{BUTTON_GET_CASES} {LANGUAGE_JAVA} тесты"
BUTTON_GET_MORE_CASES_JAVA = f"{BUTTON_GET_MORE_CASES} {LANGUAGE_JAVA} тесты"

BUTTON_GET_CASES_CURL = f"{BUTTON_GET_CASES} {LANGUAGE_CURL} тесты"
BUTTON_GET_MORE_CASES_CURL = f"{BUTTON_GET_MORE_CASES} {LANGUAGE_CURL} тесты"


TYPE_PROMPT_PYTHON = 'api_python_test_case_prompt'
TYPE_PROMPT_JAVA = 'api_java_test_case_prompt'
TYPE_PROMPT_CURL = 'api_curl_test_case_prompt'
TYPE_PROMPT_WIKI = 'test_case_prompt'


ERROR_ADD_TEST_CASE = "Ошибка при добавлении тест-кейса: "
ERROR_PROMPT_NOT_FOUND = "Промпт не найден"

class Keys:    
    GENERATED_TEXT: str = "generated_text"
    SPACE: str = " "
    EMPTY: str = ""
    TITLE = "title"

class UtilitsParsing:
    #Токен для доступа к вики
    # WIKI_TOKEN: str = "wiki_token"
    #Используется для создаиния конфлю-эклиента
    URL_WIKI: str = "https://wiki.domrf.ru"
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
    NOT_HEADERS_TIM = "ТИМ"
    NOT_HEADERS_US = "US"


class DefaultValuesLLM:
    DEF_TEMPERATURE: float = 0.4
    DEF_MAX_NEW_TOKENS: int = 1500
    DEF_REPETITION_PENALTY: float = 1.1
    DEF_FREQUENCY_PENALTY: float = 0.5

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
    TYPE_OPTION_WIKI = "Генерация тестового кейса из сценария задачи (Вики)"
    TYPE_OPTION_CURL = "Генерация тестовых кейсов API (CURL)"
    OPTIONS_LIST = [TYPE_OPTION_WIKI, TYPE_OPTION_CURL]
    


class GeneralUtilitsConsts:
    #Тип кодировки - prompts
    TYPE_ENCODING: str = "utf-8"
    #Заголовки запроса к LLM
    HEADERS: dict = {"Content-Type": "application/json", 
                            'accept': 'application/json',}
    RETRY_TRIES: int = 8
    MODEL_LOCAL_NAME: str = "local-model"


class LoggerMsg:
    NOT_IMPLEMENTED = "Потоковая генерация не поддерживается." #!!!
    ERROR_RESPONSE_LLM_MSG = 'Задайте вопрос по теме, пожалуйста' #!!!
    ERROR_RESPONSE_LLM = "Ошибка вызова модели:" #!!!
    ERROR_WIKI_GET_SCENARIO = "Ошибка получения сценария: " #!!!
        #Шаблон сообщения об ошибке
    ERROR: str = "An error %s in %s"
    #Информационное сообщение о получении обратной связи
    INFO_GET_FEEDBACK: str = "Get feedback"
    #о записи обратной связи
    INFO_WRITE_FEEDBACK: str = "Writing feedback"
    #о начале операции
    INFO_START: str = "Starting %s for: %s"
    #о завершении операции
    INFO_END: str = "Completed %s for: %s"
    #о процессе проверки
    INFO_PROCESS_CHECK: str = "Processing check %d/%d: %s"
    #о несоответствии заголовков
    WARNING_MISMATCH: str = "Title mismatch: %s vs %s"
    #Предупреждающее сообщение о некорректной структуре блока
    WARNING_BLOCK_STRUCTURE: str = "Invalid block structure for title: %s"
    #об ошибке при поиске соответствия
    ERROR_FIND_BEST_MATCH : str = "Ошибка при поиске соответствия: "
    #сообщение о значении оценки
    INFO_SCORE: str = "%s: %s, Заголовок блока: %s"
    #сообщение о ответе модели
    INFO_LLM_RESPONSE: str = "LLM Response: %s, Заголовок блока: %s"
    #сообщение о промпте
    INFO_PROMPT: str = "Prompt: %s, Заголовок блока: %s"
    #сообщение о результате до обновления
    INFO_RESULT_BEFORE_UPDATE: str = "Результат до update_result_scores: %s"
    #сообщение о результате после обновления
    INFO_RESULT_AFTER_UPDATE: str = "Результат после update_result_scores: %s"
    #сообщение о некорректной оценке
    WARNING_INVALID_RATING: str = "Invalid rating extracted for: %s"
    #сообщение о добавлении разделителя
    INFO_SEPARATOR_ADDED: str = "Добавлен разделитель для блока: %s"
    ERROR_GET_DATA_PAGE = "Ошибка получения данных страницы: "
    ERROR_EXTRACT_LINK_WIKI = "Пожалуйста, введите корректную ссылку (должна начинаться с http:// или https://)."

class GeneralValuesLLM:
    GEN_RESPONSE_TEMP: float = 0.4
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
