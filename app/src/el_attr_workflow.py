import asyncio
import base64
import time
from src.browser_config import (
    create_browser, AVAILABLE_SELECTORS, DEFAULT_SELECTORS
)
from src.auth_handler import authenticate_user
from src.element_handler import collect_elements
from src.locator_generator import (
    build_locators, add_selenide_elements, validate_and_fix_locators
)
from src.locator_utils import sanitize_selectors
from src.browser_config import (
    MAX_ELEMENTS_PER_CHUNK,
    MAX_ELEMENTS_PER_FIX_CHUNK,
    MAX_CHILDREN_ELEMENTS,
    MAX_TOTAL_ELEMENTS,
    PAGE_STABILIZE_SECONDS,
    READY_STATE_TIMEOUT_SECONDS,
)


async def _wait_page_stable(page) -> None:
    """
    Ждем, пока документ перейдет в readyState=interactive/complete,
    затем даем странице короткое время на стабилизацию динамических блоков.
    """
    async def _ready() -> bool:
        state = await page.evaluate("() => document.readyState")
        return state in ("interactive", "complete")

    started = time.perf_counter()
    while time.perf_counter() - started < READY_STATE_TIMEOUT_SECONDS:
        try:
            if await _ready():
                break
        except Exception:
            pass
        await asyncio.sleep(0.5)

    if PAGE_STABILIZE_SECONDS > 0:
        await asyncio.sleep(float(PAGE_STABILIZE_SECONDS))


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
    auth_custom_instructions: str = None,
    chunk_size: int = MAX_ELEMENTS_PER_CHUNK,
    fix_chunk_size: int = MAX_ELEMENTS_PER_FIX_CHUNK,
    max_total_elements: int = MAX_TOTAL_ELEMENTS,
    max_children_elements: int = MAX_CHILDREN_ELEMENTS,
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
            event_log: list[dict] = []
            screenshots: list[dict] = []

            def _log_event(stage: str, message: str, **extra):
                event_log.append({
                    "ts": time.time(),
                    "stage": stage,
                    "message": message,
                    **extra,
                })

            async def _capture_screenshot(name: str):
                try:
                    image_bytes = await page.screenshot(full_page=True)
                    screenshots.append({
                        "name": name,
                        "content_b64": base64.b64encode(image_bytes).decode("ascii"),
                    })
                except Exception:
                    pass

            # Создаем и запускаем браузер
            if progress_callback:
                progress_callback(0.1, "Запуск браузера...")
            
            t_total = time.perf_counter()
            t0 = time.perf_counter()
            browser = await create_browser()
            browser_start_s = time.perf_counter() - t0
            _log_event("browser_start", "Browser started", elapsed_s=browser_start_s)

            # Выполняем авторизацию, если требуется
            if needs_auth and auth_username and auth_password:
                t1 = time.perf_counter()
                await authenticate_user(
                    browser=browser,
                    url=target_url,
                    username=auth_username,
                    password=auth_password,
                    custom_instructions=auth_custom_instructions,
                    progress_callback=progress_callback,
                )
                auth_s = time.perf_counter() - t1
                
                # Agent уже работает с браузером, получаем активную страницу
                # Создаем новую страницу на том же URL для продолжения работы
                page = await browser.new_page(target_url)
                await _wait_page_stable(page)
            else:
                auth_s = None
                # Создаем страницу без авторизации
                page = await browser.new_page(target_url)
                await _wait_page_stable(page)
            await _capture_screenshot("page_loaded")
            _log_event("page_loaded", "Target page loaded")

            # Собираем элементы
            if progress_callback:
                progress_callback(0.2, "Сбор элементов со страницы...")
            
            t2 = time.perf_counter()
            elements_data, selector_stats = await collect_elements(
                page=page,
                selectors=selectors,
                prompt_description=prompt_description,
                parent_xpath=parent_xpath,
                available_selectors=AVAILABLE_SELECTORS,
                default_selectors=DEFAULT_SELECTORS,
                max_total_elements=max_total_elements,
                max_children_elements=max_children_elements,
            )
            collect_elements_s = time.perf_counter() - t2
            _log_event(
                "collect_elements",
                "Collected elements",
                elapsed_s=collect_elements_s,
                groups=len(elements_data) if isinstance(elements_data, dict) else None,
            )
            await _capture_screenshot("after_collect")

            # Генерируем локаторы
            if progress_callback:
                progress_callback(0.5, "Генерация XPath локаторов...")
            
            t3 = time.perf_counter()
            collected_locators = await build_locators(
                elements_data=elements_data,
                progress_callback=progress_callback,
                chunk_size=chunk_size,
            )
            generate_locators_s = time.perf_counter() - t3
            _log_event(
                "generate_locators",
                "Generated locator candidates",
                elapsed_s=generate_locators_s,
                count=len(collected_locators) if isinstance(collected_locators, list) else None,
            )

            # Добавляем Selenide элементы, если требуется
            if generate_selenide:
                if progress_callback:
                    progress_callback(0.7, "Генерация Selenide элементов...")
                
                collected_locators = await add_selenide_elements(
                    collected_locators=collected_locators,
                    progress_callback=progress_callback,
                    chunk_size=chunk_size,
                )

            # Валидируем и исправляем локаторы
            t4 = time.perf_counter()
            final_validated_locators, validation_stats = await validate_and_fix_locators(
                page=page,
                collected_locators=collected_locators,
                elements_data=elements_data,
                progress_callback=progress_callback,
                fix_chunk_size=fix_chunk_size,
            )
            validate_and_fix_s = time.perf_counter() - t4
            _log_event(
                "validate_and_fix",
                "Validation and fix completed",
                elapsed_s=validate_and_fix_s,
                stats=validation_stats if isinstance(validation_stats, dict) else None,
            )
            await _capture_screenshot("after_validate")
            
            # Подсчитываем статистику
            valid_count = len([
                loc for loc in final_validated_locators 
                if loc.get('exists') and loc.get('count') == 1
            ])
            total_s = time.perf_counter() - t_total
            
            if progress_callback:
                progress_callback(1.0, "Готово!")

            return {
                "locators": final_validated_locators,
                "selector_stats": selector_stats,
                "valid_count": valid_count,
                "total_count": len(final_validated_locators),
                "elements_data": elements_data,
                "timings": {
                    "browser_start_s": browser_start_s,
                    "auth_s": auth_s,
                    "collect_elements_s": collect_elements_s,
                    "generate_locators_s": generate_locators_s,
                    "validate_and_fix_s": validate_and_fix_s,
                    "total_s": total_s,
                },
                "validation_stats": validation_stats,
                "limits": {
                    "chunk_size": chunk_size,
                    "fix_chunk_size": fix_chunk_size,
                    "max_total_elements": max_total_elements,
                    "max_children_elements": max_children_elements,
                },
                "artifacts": {
                    "events": event_log,
                    "screenshots": screenshots,
                },
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
    auth_custom_instructions: str = None,
    chunk_size: int = MAX_ELEMENTS_PER_CHUNK,
    fix_chunk_size: int = MAX_ELEMENTS_PER_FIX_CHUNK,
    max_total_elements: int = MAX_TOTAL_ELEMENTS,
    max_children_elements: int = MAX_CHILDREN_ELEMENTS,
):
    """
    Синхронная обертка для основной функции генерации локаторов.
    """
    sanitized = (sanitize_selectors(selectors, DEFAULT_SELECTORS, AVAILABLE_SELECTORS) 
                if prompt_description is None and parent_xpath is None else selectors)
    
    return asyncio.run(main(
        url, sanitized, prompt_description, parent_xpath, generate_selenide, 
        progress_callback, needs_auth, auth_username, auth_password, auth_custom_instructions,
        chunk_size, fix_chunk_size, max_total_elements, max_children_elements,
    ))