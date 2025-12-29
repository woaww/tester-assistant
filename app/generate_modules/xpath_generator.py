from pathlib import Path
from src.logger import log_function_call
from src.text_constants import Keys
from src.utils import load_prompts
from src.utils import generate_response_async
from src.text_constants import LLM_URL
import openai
import json


PROMPTS = load_prompts()
PROMPT_DUMP_PATH = Path(__file__).resolve().parent.parent / "xpath_prompt.txt"
TOOLS_LOCATORS = [
    {
        "type": "function",
        "function": {
            "name": "get_elements_information",
            "description": "Получение массива элементов с xpath и description",
            "parameters": {
                "type": "object",
                "properties": {
                    "elements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "xpath": {"type": "string"},
                                "description": {"type": "string"}
                            },
                            "required": ["xpath", "description"]
                        }
                    }
                },
                "required": ["elements"]
            }
        }
    }
]
TOOLS_SELENIDE = [
    {
        "type": "function",
        "function": {
            "name": "get_selenide_elements",
            "description": "Получение массива Selenide элементов по xpath и description",
            "parameters": {
                "type": "object",
                "properties": {
                    "elements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "xpath": {"type": "string"},
                                "description": {"type": "string"},
                                "selenide_element": {"type": "string"},
                            },
                            "required": ["xpath", "description", "selenide_element"]
                        }
                    }
                },
                "required": ["elements"]
            }
        }
    }
]

TOOLS_XPATH_FIX = [
    {
        "type": "function",
        "function": {
            "name": "fix_xpath_locators",
            "description": "Исправление некорректных XPath локаторов",
            "parameters": {
                "type": "object",
                "properties": {
                    "elements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "xpath": {"type": "string"},
                                "description": {"type": "string"}
                            },
                            "required": ["xpath", "description"]
                        }
                    }
                },
                "required": ["elements"]
            }
        }
    }
]


@log_function_call()
def format_prompt(prompt_template, **kwargs):
    return prompt_template.format(**kwargs)


def save_prompt_snapshot(prompt: str) -> None:
    PROMPT_DUMP_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROMPT_DUMP_PATH.write_text(prompt, encoding="utf-8")


@log_function_call()
async def generate_xpath_locators(elements_data: dict) -> str:
    prompt_template = PROMPTS.get("xpath_generator_prompt", {}).get(
        Keys.CONTENT, Keys.EMPTY)
    
    # Преобразуем словарь в JSON-строку для промпта
    json_data = json.dumps(elements_data, ensure_ascii=False, separators=(',', ':'))
    
    formatted_prompt = format_prompt(
        prompt_template=prompt_template,
        elements_data=json_data
    )
    # save_prompt_snapshot(formatted_prompt) 
    
    response = await generate_response_async(prompt_input=formatted_prompt, temp=0.2,max_tokens=5000, repetition_penalty=1.2, frequency_penalty=0.4)
    
    return response


@log_function_call()
async def generate_xpath_locators_structured(elements_data: list[dict], max_retries: int = 3) -> list[dict]:
    prompt_template = PROMPTS.get("xpath_generator_prompt", {}).get(
        Keys.CONTENT, Keys.EMPTY)

    json_data = json.dumps(elements_data, ensure_ascii=False, separators=(',', ':'))

    formatted_prompt = format_prompt(
        prompt_template=prompt_template,
        elements_data=json_data
    )
    
    # save_prompt_snapshot(formatted_prompt) 

    client = openai.AsyncOpenAI(
        api_key="-",
        base_url=LLM_URL,
    )
    
    for attempt in range(max_retries):
        try:
            resp = await client.chat.completions.create(
                model="tgi",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты – опытный системный аналитик и специалист по веб-тестированию и автоматизации."
                    },
                    {"role": "user", "content": formatted_prompt},
                ],
                tools=TOOLS_LOCATORS,
                tool_choice="auto",
                max_tokens=1000,
                temperature=0.05,
            )

            choice = resp.choices[0]
            tool_calls = choice.message.tool_calls or []
            if not tool_calls:
                raise ValueError("LLM не вернул вызов инструмента get_elements_information")

            arguments = tool_calls[0].function.arguments
            payload = json.loads(arguments)

            elements = payload.get("elements")
            if not isinstance(elements, list):
                raise ValueError("Ответ не содержит массива elements")

            normalized = []
            for item in elements:
                if not isinstance(item, dict):
                    continue
                xpath = item.get("xpath", "")
                description = item.get("description", "")
                normalized.append({"xpath": xpath, "description": description})

            return normalized
            
        except Exception as e:
            print(f"Ошибка при генерации XPath (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("Повторная попытка...")
                continue
            else:
                print("Все попытки исчерпаны, возвращаем пустой список")
                return []


@log_function_call()
async def generate_selenide_elements_structured(locators: list[dict], max_retries: int = 3) -> list[dict]:
    prompt_template = PROMPTS.get("selenide_element_prompt", {}).get(
        Keys.CONTENT, Keys.EMPTY)

    json_data = json.dumps(locators, ensure_ascii=False, separators=(',', ':'))

    formatted_prompt = format_prompt(
        prompt_template=prompt_template,
        locators=json_data
    )

    # save_prompt_snapshot(formatted_prompt) 

    client = openai.AsyncOpenAI(
        api_key="-",
        base_url=LLM_URL,
    )
    
    for attempt in range(max_retries):
        try:
            resp = await client.chat.completions.create(
                model="tgi",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты – опытный инженер по автоматизации тестирования."
                    },
                    {"role": "user", "content": formatted_prompt},
                ],
                tools=TOOLS_SELENIDE,
                tool_choice="auto",
                max_tokens=3000,
                temperature=0.15,
            )

            choice = resp.choices[0]
            tool_calls = choice.message.tool_calls or []
            if not tool_calls:
                raise ValueError("LLM не вернул вызов инструмента get_selenide_elements")

            arguments = tool_calls[0].function.arguments
            payload = json.loads(arguments)

            elements = payload.get("elements")
            if not isinstance(elements, list):
                raise ValueError("Ответ не содержит массива elements")

            normalized = []
            for item in elements:
                if not isinstance(item, dict):
                    continue
                normalized.append({
                    "xpath": item.get("xpath", ""),
                    "description": item.get("description", ""),
                    "selenide_element": item.get("selenide_element", ""),
                })

            return normalized
            
        except Exception as e:
            print(f"Ошибка при генерации Selenide (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("Повторная попытка...")
                continue
            else:
                print("Все попытки исчерпаны, возвращаем исходные данные")
                return locators

@log_function_call()
async def generate_selenide_elements(locators: list[dict]) -> str:
    prompt_template = PROMPTS.get("selenide_element_prompt", {}).get(
        Keys.CONTENT, Keys.EMPTY)

    json_data = json.dumps(locators, ensure_ascii=False, separators=(',', ':'))

    formatted_prompt = format_prompt(
        prompt_template=prompt_template,
        locators=json_data
    )
    # save_prompt_snapshot(formatted_prompt)

    response = await generate_response_async(prompt_input=formatted_prompt, temp=0.15, max_tokens=3000, repetition_penalty=1.2, frequency_penalty=0.4)
    return response


@log_function_call()
async def fix_invalid_xpath_locators(
    invalid_locators: list[dict], 
    elements_data: list[dict], 
    max_retries: int = 3
) -> list[dict]:
    """
    Исправляет некорректные XPath локаторы через LLM.
    
    Args:
        invalid_locators: Список некорректных локаторов с информацией о валидации
        elements_data: Данные об элементах, соответствующие локаторам по индексу
        max_retries: Максимальное количество попыток
    
    Returns:
        Список исправленных локаторов
    """
    if not invalid_locators:
        return []
    
    # Подготавливаем данные для исправления - сопоставляем каждый локатор с его элементом
    fix_data = []
    for i, locator in enumerate(invalid_locators):
        # Берем соответствующий элемент по индексу, если он есть
        element_data = elements_data[i] if i < len(elements_data) else {}
        
        fix_data.append({
            "original_xpath": locator.get("xpath", ""),
            "description": locator.get("description", ""),
            "validation_result": {
                "exists": locator.get("exists", False),
                "count": locator.get("count", 0)
            },
            "element_data": element_data
        })
    
    prompt_template = PROMPTS.get("xpath_fix_prompt", {}).get(Keys.CONTENT, "")
    if not prompt_template:
        print("Промпт для исправления XPath не найден, используем базовый")
        prompt_template = """
        Исправь некорректные XPath локаторы на основе данных об элементах и результатов валидации.
        
        Данные для исправления: {fix_data}
        
        Требования:
        1. Если локатор не найден (count = 0), создай новый на основе данных элемента
        2. Если локатор находит больше 1 элемента (count > 1), сделай его более специфичным
        3. Используй только относительные XPath
        4. Каждый локатор должен находить ровно 1 элемент
        5. ВАЖНО: верни ровно столько локаторов, сколько получил на вход
        """
    
    json_data = json.dumps(fix_data, ensure_ascii=False, separators=(',', ':'))
    formatted_prompt = format_prompt(
        prompt_template=prompt_template,
        fix_data=json_data
    )
    
    # save_prompt_snapshot(formatted_prompt)
    
    client = openai.AsyncOpenAI(
        api_key="-",
        base_url=LLM_URL,
    )
    
    for attempt in range(max_retries):
        try:
            resp = await client.chat.completions.create(
                model="tgi",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты – опытный системный аналитик и специалист по веб-тестированию. Твоя задача - исправить некорректные XPath локаторы. ВАЖНО: количество исправленных локаторов должно точно соответствовать количеству входных."
                    },
                    {"role": "user", "content": formatted_prompt},
                ],
                tools=TOOLS_XPATH_FIX,
                tool_choice="auto",
                max_tokens=2000,
                temperature=0.1,
            )

            choice = resp.choices[0]
            tool_calls = choice.message.tool_calls or []
            if not tool_calls:
                raise ValueError("LLM не вернул вызов инструмента fix_xpath_locators")

            arguments = tool_calls[0].function.arguments
            payload = json.loads(arguments)

            elements = payload.get("elements")
            if not isinstance(elements, list):
                raise ValueError("Ответ не содержит массива elements")

            # Нормализуем элементы
            fixed_locators = []
            for item in elements:
                if not isinstance(item, dict):
                    continue
                xpath = item.get("xpath", "")
                description = item.get("description", "")
                fixed_locators.append({"xpath": xpath, "description": description})

            # Проверяем соответствие количества
            if len(fixed_locators) != len(invalid_locators):
                print(f"Предупреждение: LLM вернул {len(fixed_locators)} локаторов вместо ожидаемых {len(invalid_locators)}")
                
                # Дополняем или обрезаем до нужного количества
                if len(fixed_locators) < len(invalid_locators):
                    # Дополняем исходными локаторами
                    for i in range(len(fixed_locators), len(invalid_locators)):
                        fixed_locators.append({
                            "xpath": invalid_locators[i].get("xpath", ""),
                            "description": invalid_locators[i].get("description", "")
                        })
                else:
                    # Обрезаем до нужного количества
                    fixed_locators = fixed_locators[:len(invalid_locators)]

            return fixed_locators
            
        except Exception as e:
            print(f"Ошибка при исправлении XPath (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("Повторная попытка...")
                continue
            else:
                print("Все попытки исчерпаны, возвращаем исходные локаторы")
                return [{"xpath": loc.get("xpath", ""), "description": loc.get("description", "")} for loc in invalid_locators]

