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
async def generate_xpath_locators_structured(elements_data: dict) -> list[dict]:
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
        max_tokens=4000,
        temperature=0.2,
    )

    choice = resp.choices[0]
    tool_calls = choice.message.tool_calls or []
    if not tool_calls:
        raise ValueError("LLM не вернул вызов инструмента get_elements_information")

    arguments = tool_calls[0].function.arguments
    try:
        payload = json.loads(arguments)
    except Exception as e:
        raise ValueError(f"Не удалось распарсить arguments как JSON: {e}")

    elements = payload.get("elements")
    if not isinstance(elements, list):
        raise ValueError("Ответ не содержит массива elements")

    # Нормализуем элементы (xpath, description)
    normalized = []
    for item in elements:
        if not isinstance(item, dict):
            continue
        xpath = item.get("xpath", "")
        description = item.get("description", "")
        normalized.append({"xpath": xpath, "description": description})

    return normalized


@log_function_call()
async def generate_selenide_elements_structured(locators: list[dict]) -> list[dict]:
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
    try:
        payload = json.loads(arguments)
    except Exception as e:
        raise ValueError(f"Не удалось распарсить arguments как JSON: {e}")

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

