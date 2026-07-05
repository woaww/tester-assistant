from dotenv import load_dotenv

load_dotenv()


class Keys:
    EMPTY: str = ""
    CONTENT: str = "content"

class DefaultValuesLLM:
    DEF_TEMPERATURE: float = 0.1
    DEF_MAX_NEW_TOKENS: int = 2500
    DEF_REPETITION_PENALTY: float = 1.2
    DEF_FREQUENCY_PENALTY: float = 0.9

class GeneralUtilitsConsts:
    RETRY_TRIES: int = 3


class LoggerMsg:
    INFO_START: str = "Starting"
    INFO_END: str = "Completed"
    ERROR: str = "An error"


class GeneralValuesLLM:
    GEN_RESPONSE_TEMP: float = 0.15
    GEN_RESPONSE_MAX_TOKENS: int = 1000
    GEN_RESPONSE_REPETITION_PENALTY: float = 1.2
    GEN_RESPONSE_FREQUENCY_PENALTY: float = 0.4
    GEN_RESPONSE_TOP_K: int = 60
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
            "start": 0.000000001,
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
