import asyncio
import logging

from browser_use import Agent, Browser

from src.browser_config import create_llm
from src.utils import load_prompts

_log = logging.getLogger(__name__)


async def authenticate_user(
    browser: Browser,
    url: str,
    username: str,
    password: str,
    custom_instructions: str | None = None,
    progress_callback=None,
) -> None:
    """
    Выполняет авторизацию пользователя на указанной странице.
    """
    if progress_callback:
        progress_callback(0.15, "Выполнение авторизации...")

    sensitive_data = {"username": username, "password": password}
    auth_task = _build_auth_task(url, custom_instructions)
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
    
    try:
        await asyncio.wait_for(auth_agent.run(), timeout=120)
        await asyncio.sleep(3)
    except asyncio.TimeoutError:
        _log.warning("Авторизация: превышен лимит времени")
    except Exception as e:
        _log.warning("Авторизация: ошибка агента: %s", e)


def _build_auth_task(url: str, custom_instructions: str | None = None) -> str:
    """Формирует задачу для агента: базовый промпт auth_custom + опциональные шаги пользователя."""
    prompts = load_prompts()
    auth_prompt = prompts.get("auth_custom", {}).get("content", "")

    task = f"Перейди на страницу {url} и выполни авторизацию.\n\n{auth_prompt}"

    if custom_instructions:
        task += f"\n\nПОЛЬЗОВАТЕЛЬСКИЕ ИНСТРУКЦИИ:\n{custom_instructions}"

    return task