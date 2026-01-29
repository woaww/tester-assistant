import asyncio
from browser_use import Browser, Agent
from src.browser_config import create_llm
from src.utils import load_prompts


AUTH_TYPES = {
    "gosuslugi": "Госуслуги",
    "domrf_employee": "Сотрудники ГК ДОМ.РФ", 
    "eisjks_bank": "ЕИСЖС ID (Банк)",
    "eisjks_supplier": "ЕИСЖС ID (Поставщик)",
    "custom": "Пользовательский сценарий"
}


async def authenticate_user(
    browser: Browser,
    url: str,
    username: str,
    password: str,
    auth_type: str = "custom",
    organization: str = None,
    custom_instructions: str = None,
    progress_callback=None
) -> None:
    """
    Выполняет авторизацию пользователя на указанной странице.
    """
    if progress_callback:
        progress_callback(0.15, "Выполнение авторизации...")
    
    # Создаем данные для авторизации
    sensitive_data = {
        'username': username,
        'password': password
    }
    
    # Генерируем задачу для Agent'а
    auth_task = _build_auth_task(url, auth_type, organization, custom_instructions)
    
    # Создаем и запускаем Agent для авторизации
    auth_llm = create_llm()
    auth_agent = Agent(
        task=auth_task,
        sensitive_data=sensitive_data,
        use_vision=False,
        llm=auth_llm,
        browser=browser,
        max_actions_per_step=3, 
        max_steps=15,
    )
    
    # Запускаем авторизацию с таймаутом
    try:
        await asyncio.wait_for(auth_agent.run(), timeout=120)
        await asyncio.sleep(3)
    except asyncio.TimeoutError:
        print("Авторизация превысила лимит времени ")
    except Exception as e:
        print(f" Ошибка при авторизации: {e}")


def _build_auth_task(url: str, auth_type: str, organization: str = None, custom_instructions: str = None) -> str:
    """
    Создает задачу для авторизации.
    """
    # Загружаем промпты из файла
    prompts = load_prompts()
    
    # Определяем ключ промпта
    prompt_key = f"auth_{auth_type}"
    auth_prompt = prompts.get(prompt_key, {}).get('content', '')

    task = f'Перейди на страницу {url} и выполни авторизацию.\n\n{auth_prompt}'

    if organization and auth_type in ['gosuslugi', 'eisjks_bank', 'eisjks_supplier']:
        task += f'\n\nВАЖНО: При выборе организации выбери "{organization}".'

    if auth_type == 'custom' and custom_instructions:
        task += f'\n\nПОЛЬЗОВАТЕЛЬСКИЕ ИНСТРУКЦИИ:\n{custom_instructions}'
    
    return task