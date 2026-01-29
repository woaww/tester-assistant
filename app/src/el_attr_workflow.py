import asyncio
from src.browser_config import (
    create_browser, AVAILABLE_SELECTORS, DEFAULT_SELECTORS
)
from src.auth_handler import authenticate_user
from src.element_handler import collect_elements
from src.locator_generator import (
    build_locators, add_selenide_elements, validate_and_fix_locators
)
from src.locator_utils import sanitize_selectors


async def main(
    url: str = None,
    selectors: list[str] = None,
    prompt_description: str = None,
    parent_xpath: str = None,
    generate_selenide: bool = False,
    progress_callback=None,
    needs_auth: bool = False,
    auth_username: str = None,
    auth_password: str = None,
    auth_type: str = "custom",
    auth_organization: str = None,
    auth_custom_instructions: str = None,
):
    """
    Основная функция генерации локаторов.
    """
    target_url = url
    if not target_url or not target_url.strip():
        raise ValueError("URL страницы обязателен для заполнения")
    
    last_error = None
    RETRIES = 3

    for attempt in range(RETRIES):
        browser = None
        try:
            # Создаем и запускаем браузер
            if progress_callback:
                progress_callback(0.1, "Запуск браузера...")
            
            browser = await create_browser()

            # Выполняем авторизацию, если требуется
            if needs_auth and auth_username and auth_password:
                await authenticate_user(
                    browser=browser,
                    url=target_url,
                    username=auth_username,
                    password=auth_password,
                    auth_type=auth_type,
                    organization=auth_organization,
                    custom_instructions=auth_custom_instructions,
                    progress_callback=progress_callback
                )
                
                # Agent уже работает с браузером, получаем активную страницу
                # Создаем новую страницу на том же URL для продолжения работы
                page = await browser.new_page(target_url)
                await asyncio.sleep(3)
            else:
                # Создаем страницу без авторизации
                page = await browser.new_page(target_url)
                await asyncio.sleep(10)

            # Собираем элементы
            if progress_callback:
                progress_callback(0.2, "Сбор элементов со страницы...")
            
            elements_data, selector_stats = await collect_elements(
                page=page,
                selectors=selectors,
                prompt_description=prompt_description,
                parent_xpath=parent_xpath,
                available_selectors=AVAILABLE_SELECTORS,
                default_selectors=DEFAULT_SELECTORS
            )

            # Генерируем локаторы
            if progress_callback:
                progress_callback(0.5, "Генерация XPath локаторов...")
            
            collected_locators = await build_locators(
                elements_data=elements_data,
                progress_callback=progress_callback
            )

            # Добавляем Selenide элементы, если требуется
            if generate_selenide:
                if progress_callback:
                    progress_callback(0.7, "Генерация Selenide элементов...")
                
                collected_locators = await add_selenide_elements(
                    collected_locators=collected_locators,
                    progress_callback=progress_callback
                )

            # Валидируем и исправляем локаторы
            final_validated_locators = await validate_and_fix_locators(
                page=page,
                collected_locators=collected_locators,
                elements_data=elements_data,
                progress_callback=progress_callback
            )
            
            # Подсчитываем статистику
            valid_count = len([
                loc for loc in final_validated_locators 
                if loc.get('exists') and loc.get('count') == 1
            ])
            
            if progress_callback:
                progress_callback(1.0, "Готово!")

            return {
                "locators": final_validated_locators,
                "selector_stats": selector_stats,
                "valid_count": valid_count,
                "total_count": len(final_validated_locators),
            }

        except Exception as e:
            last_error = e
            msg = str(e)
            if ("Document needs to be requested first" in msg) or ("element_highlight_index" in msg):
                continue
            raise
        finally:
            if browser:
                try:
                    await browser.stop()
                except Exception:
                    pass

    if last_error:
        raise last_error


def run_el_attr_workflow(
    url: str = None,
    selectors: list[str] = None,
    prompt_description: str = None,
    parent_xpath: str = None,
    generate_selenide: bool = False,
    progress_callback=None,
    needs_auth: bool = False,
    auth_username: str = None,
    auth_password: str = None,
    auth_type: str = "custom",
    auth_organization: str = None,
    auth_custom_instructions: str = None,
):
    """
    Синхронная обертка для основной функции генерации локаторов.
    """
    sanitized = (sanitize_selectors(selectors, DEFAULT_SELECTORS, AVAILABLE_SELECTORS) 
                if prompt_description is None and parent_xpath is None else selectors)
    
    return asyncio.run(main(
        url, sanitized, prompt_description, parent_xpath, generate_selenide, 
        progress_callback, needs_auth, auth_username, auth_password, auth_type,
        auth_organization, auth_custom_instructions
    ))