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

HEADER_SETTINGS = "Настройки"
CURRENT_GENERATION_PARAMETERS = "Текущие параметры генерации:"

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

SPLIT_SIGN = ","

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

# можно добаавить проверку на адрес для яндекса

FEEDBACK_STATS = "### 📊 Статистика оценок"
ALL_EVALUATION = "**Всего оценок:**"
NEGATIVE_EVALUATION = "**Отрицательных:**"
POSITIVE_EVALUATION = "**Положительных:**"
INFO_EVALUATION = "Нет данных для отображения."


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



class Separatiors:
    sep_cases: str = '---\n\n'+'---\n\n'+'---\n\n'

class PostProcStr:
    general_text_0: str = "Эти тесты покрывают основные сценарии использования метода,"
    general_text_1: str = "включая проверку существования заявления, корректность передаваемых данных,"
    general_text_2: str = "авторизацию и использование правильных HTTP-методов."
    undefined = "undefined"
    prompt_text_0: str = "Обратите внимание на то, что каждый тест-кейс содержит уникальный запрос и описание,"
    prompt_text_1: str = "которое помогает понять его цель и ожидаемый результат."
    prompt_text_3: str = "Тест-кейсы должны быть уникальными и покрывать все возможные сценарии использования API."
    resp_text_0: str = "Note that the actual status codes "
    resp_text_1: str = "and responses may vary depending on the implementation of the API being tested. " 
    resp_text_2: str = "The above code assumes a successful response for valid requests "
    resp_text_3: str = "and an error response for invalid or non-existent full-statement-id."
    resp_text_4: str = "Note that I've used assertions to check the expected behavior of each test case."
    resp_text_5: str = "You can replace these assertions with your own logic"
    resp_text_6: str = " or use a testing framework like pytest to run these tests automatically."
    resp_text_7: str = "Here are the rewritten test cases in Python using the requests library:"
    resp_text_8: str = "This solution provides a set of JUnit tests for each of the given"
    resp_text_9: str = " cURL commands using the RestAssured library in Java."
    resp_text_10: str = " Each method represents one test case,."
    resp_text_11: str = " with appropriate headers and request bodies included as necessary."
    resp_text_12: str = " Assertions can be added within the methods to validate the expected responses from the server."
    LIST_DEL_STR: list = [general_text_2, general_text_1, general_text_0, undefined,
                          prompt_text_1, prompt_text_0, prompt_text_3, resp_text_0,
                          resp_text_1, resp_text_2, resp_text_3,resp_text_4,
                          resp_text_5, resp_text_6, resp_text_7, resp_text_8,
                          resp_text_9, resp_text_10, resp_text_11, resp_text_12]

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
