from src.numerical_constants import (DEFAULT_TEMPERATURE, DEFAULT_MAX_NEW_TOKENS, 
                            DEFAULT_REPETITION_PENALTY, DEFAULT_FREQUENCY_PENALTY)

# Logger constatns

LOG_FORMAT = ('%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] '
              '%(message)s - Function: %(funcName)s')
LOG_DATETIME_FORMAT = '%Y-%m-%d:%H:%M:%S'

# Константны для display settings

SEPARATION_STR  = "---"

SELECT_TEMPERATURE_STR = "Задать температуру LLM"
SELECT_MAX_NEW_TOKENS_STR = "Задать максимальное количество токенов LLM"
SELECT_REPETITION_PENALTY_STR = "Задать repetition penalty LLM"
SELECT_FREQUENCY_PENALTY_STR = "Задать frequency penalty LLM"
SELECTS_LIST = [SELECT_TEMPERATURE_STR, SELECT_MAX_NEW_TOKENS_STR,
                SELECT_REPETITION_PENALTY_STR, SELECT_FREQUENCY_PENALTY_STR]

DESCRIPTION_FOR_TEMPRATURE ="Температура (0.0 - 1.0):\n" \
            "- Низкая (ближе к 0) = более предсказуемые ответы\n" \
            "- Высокая (ближе к 1) = более креативные, разнообразные, но рискованные ответы\n" \
            "- Представьте как регулятор творческой свободы модели"
DESCRIPTION_FOR_MAX_NEW_TOKENS = "Максимальное количество токенов:\n"\
            "- Ограничивает длину ответа\n"\
            "- Один токен ≈ 4 символа или часть слова\n"\
            "- Чем больше токенов, тем длиннее может быть ответ"       
DESCRIPTION_FOR_REPETITION_PENALTY = "Repetition Penalty (штраф за повторения):\n"\
            "- Предотвращает повторение одних и тех же фраз\n"\
            "- Высокое значение = модель старается избегать повторений\n"\
            "- Низкое значение = возможны повторы"
DESCRIPTION_FOR_FREQUENCY_PENALTY = "Frequency Penalty (штраф за частоту):\n"\
            "- Снижает вероятность использования часто встречающихся слов\n"\
            "- Высокое значение = более редкие и уникальные слова\n"\
            "- Низкое значение = более знакомые слова и фразы"

LABEL_FOR_TEMPERATURE = f"Температура: {DEFAULT_TEMPERATURE}"
LABEL_FOR_MAX_NEW_TOKENS = f"Максимальное количество токенов: {DEFAULT_MAX_NEW_TOKENS}"
LABEL_FOR_REPETITION_PENALTY = f"Repetition penalty: {DEFAULT_REPETITION_PENALTY}"
LABEL_FOR_FREQUENCY_PENALTY = f"Frequency penalty: {DEFAULT_FREQUENCY_PENALTY}"

HEADER_SETTINGS = "Настройки"
CURRENT_GENERATION_PARAMETERS = "Текущие параметры генерации:"
CHOOSE_PROMPT = "Задайте промпт:"
YOUR_CHOOSE = "Вы выбрали:"

AUTH_LIST = [
    "Ввод токенов",
    "Удаление токенов",
]

# Константны для form logic 

ITEM_TO_ANALYZE = "тестировщиков" #меняеется в зависимости от проекта
INIT_CHAT = (f"Добрый день! Для анализа {ITEM_TO_ANALYZE} необходима ссылка на страницу в wiki или текст."
            " Спасибо!")
CHAT_INPUT = "Введите ссылку на страницу в wiki:"
ERROR_MSG = "Пожалуйста, введите корректную ссылку (должна начинаться с http:// или https://)."
PART_OF_ANSWER = "Средняя оценка по всем блокам: "
BUTTON_RESET = "🔄 Сбросить к дефолтам"
SPINNER = "Thinking..."
BUTTON_GET_ANSWER = "Получить ответ"
SUCCESS_MSG = "Готово!"
RESULT_MSG = "## 🧠 Ответ ассистента:"
EVAL_ANSWER_MSG = "## Оцените ответ"
TEXT_AREA_FEEDBACK = "Оставьте ваш комментарий (необязательно)"
TEXT_AREA_EMAIL = "Ваша электронная почта (обязательно)"


# Константны для pages
CHAT_ASSISTENT = "Ассистент тестировщиков"
TITLE_MAIN_PAGE = f"🤗💬 {CHAT_ASSISTENT}"
PAGE_HOME = CHAT_ASSISTENT

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

PROMPT_EXIST_CASES = "\n\nСуществующие кейсы:\n"

# Error messages
# USER_ERROR_MSG = (
#         "Кажется, что-то сломалось ;("
#         "Попробуйте сначала посмотреть [сюда](https://wiki.domrf.ru/pages/viewpage.action?pageId=350025923)."
#         " Вероятно, Ваши бизнес-требования не совпадают с заданным шаблоном.",
#         "Передайте **привет** моим разработчикам вместе со ссылкой,"
#         "которую отправляли мне, спасибо!"
#     )
# TECH_MESSAGE = (
#         "Проблема возникла в процессе выполнения операции."
#         "Подробности ошибки были записаны в журнал."
#     )

MODEL_LOCAL_NAME = "local-model" #!!!

ERROR_NOTIMPLEMENTEDERROR = "Потоковая генерация не поддерживается." #!!!
ERROR_RESPONSE_LLM_MSG = 'Задайте вопрос по теме, пожалуйста' #!!!
ERROR_RESPONSE_LLM = "Ошибка вызова модели:" #!!!
ERROR_WIKI_GET_SCENARIO = "Ошибка получения сценария: " #!!!
ERROR_GET_DATA_PAGE = "Ошибка получения данных страницы: "
ERROR_EXTRACT_LINK_WIKI = "Введите id страницы в формате pageId={id}, пример - pageId=246777612"
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

ST_WARNING_MSG_WIKI = "Для работы с Wiki необходимо ввести токен."
ST_WARNING_MSG_JIRA = "Для работы с Jira необходимо ввести токен."
WIKI_TOKEN_NAME = "Wiki токен"
JIRA_TOKEN_NAME = "Jira токен"
ST_REMOVED_TOKENS = "Удаление токенов"
ST_JIRA_TOKEN_REMOVED = f"{JIRA_TOKEN_NAME} удалён."
ST_WIKI_TOKEN_REMOVED = f"{WIKI_TOKEN_NAME} удалён."
ST_JIRA_TOKEN_REMOVED_QA = f"Удалить {JIRA_TOKEN_NAME}"
ST_WIKI_TOKEN_REMOVED_QA = f"Удалить {WIKI_TOKEN_NAME}"

INPUT_TOKENS = "Ввод токенов"
ST_TOKEN_SAVED = "Токены сохранены."
ST_TOKEN_SAVED_QA = "Сохранить токены"
TYPE_TOKENS = "password"

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

TYPE_OPTION_WIKI = "Генерация тестового кейса из сценария задачи (Вики)"
TYPE_OPTION_CURL = "Генерация тестовых кейсов API (CURL)"
TYPE_OPTION_JAVA = "Генерация тестовых кейсов API (Java + RestAssured)"
TYPE_OPTION_PYTHON = "Генерация тестовых кейсов API (Python + Requests)"
# TYPE_JUST_API = f"Генерация тестовых кейсов для проверки API метода"

OPTIONS_LIST = [TYPE_OPTION_WIKI, TYPE_OPTION_CURL, TYPE_OPTION_JAVA, TYPE_OPTION_PYTHON]

BUTTON_GET_CASES = "Сгенерировать кейсы"
BUTTON_GET_MORE_CASES = "Сгенерировать ещё кейсы"

BUTTON_GET_CASES_PYTHON = f"{BUTTON_GET_CASES} {LANGUAGE_PYTHON} тесты"
BUTTON_GET_MORE_CASES_PYTHON = f"{BUTTON_GET_MORE_CASES} {LANGUAGE_PYTHON} тесты"

BUTTON_GET_CASES_JAVA = f"{BUTTON_GET_CASES} {LANGUAGE_JAVA} тесты"
BUTTON_GET_MORE_CASES_JAVA = f"{BUTTON_GET_MORE_CASES} {LANGUAGE_JAVA} тесты"

BUTTON_GET_CASES_CURL = f"{BUTTON_GET_CASES} {LANGUAGE_CURL} тесты"
BUTTON_GET_MORE_CASES_CURL = f"{BUTTON_GET_MORE_CASES} {LANGUAGE_CURL} тесты"

DSCR_METHOD = "Метод (GET, POST и т.д.)"
DSCR_ENDPOINT = "Endpoint"
DSCR_BASE_URL = "Базовый URL"
DSCR_BASE_URL_VALUE = "https://api.example.com"
DSCR_COUNT = "Количество кейсов"

TYPE_PROMPT_PYTHON = 'api_python_test_case_prompt'
TYPE_PROMPT_JAVA = 'api_java_test_case_prompt'
TYPE_PROMPT_CURL = 'api_curl_test_case_prompt'
TYPE_PROMPT_WIKI = 'test_case_prompt'

NUMBER_OF_CASES = "Количество кейсов"


ERROR_ADD_TEST_CASE = "Ошибка при добавлении тест-кейса: "
ERROR_PROMPT_NOT_FOUND = "Промпт не найден"
# ERROR_NOT_DSCR = "Пожалуйста, введите описание задачи."