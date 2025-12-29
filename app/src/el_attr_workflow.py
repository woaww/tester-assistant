import asyncio
import os
import sys
import json

from dotenv import load_dotenv
from browser_use import BrowserSession, BrowserProfile, ChatOpenAI

from generate_modules.xpath_generator import (
    generate_xpath_locators_structured,
    generate_selenide_elements_structured,
    fix_invalid_xpath_locators,
)
from src.element_extraction import extract_element_data
from src.locator_utils import (
    chunk_list,
    sanitize_selectors,
    extract_locators_from_response,
    validate_locators_on_page,
    filter_invalid_locators,
)


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


BROWSER_HEADLESS = False
BROWSER_DISABLE_SECURITY = True
BROWSER_ARGS = [
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--disable-setuid-sandbox",
    "--disable-web-security",
]

DEFAULT_URL = "https://portal.apps.k8s.dev.domoy.ru"
MAX_ELEMENTS_PER_CHUNK = 10
MAX_ELEMENTS_PER_FIX_CHUNK = 10  # Меньший размер чанка для исправления локаторов
AVAILABLE_SELECTORS = [
    "a", "abbr", "address", "article", "aside", "audio", "b", "bdi", "bdo", "blockquote",
    "body", "br", "button", "canvas", "caption", "cite", "code", "col", "colgroup", "data",
    "datalist", "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt", "em", "embed",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5",
    "h6", "header", "hr", "i", "iframe", "img", "input", "ins", "kbd", "label", "legend",
    "li", "main", "map", "mark", "menu", "meter", "nav", "noscript", "object", "ol",
    "optgroup", "option", "output", "p", "picture", "pre", "progress", "q", "rp", "rt",
    "ruby", "s", "samp", "section", "select", "small", "source", "span", "strong", "sub",
    "summary", "sup", "svg", "table", "tbody", "td", "template", "textarea", "tfoot",
    "th", "thead", "time", "tr", "track", "u", "ul", "var", "video", "wbr",
]

DEFAULT_SELECTORS = ["span"]


load_dotenv()


def create_llm(temperature: float = 0.7):
    return ChatOpenAI(
        model="gpt",
        api_key="-",
        base_url="http://localhost:8000/v1",
        temperature=temperature,
    )


async def _get_element_by_prompt_with_timeout(page, prompt: str, llm, timeout: float = 60.0):
    try:
        await asyncio.sleep(60)
        return await asyncio.wait_for(page.get_element_by_prompt(prompt, llm=llm), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Не удалось найти элемент по описанию за {timeout} сек.")


async def _generate_selenide_structured_with_timeout(data_chunk: list[dict], timeout: float = 180.0):
    try:
        return await asyncio.wait_for(generate_selenide_elements_structured(data_chunk), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Генерация SelenideElement (structured) превысила тайм-аут {timeout} сек.")


def build_browser_profile() -> BrowserProfile:
    browser_profile = BrowserProfile(
        headless=BROWSER_HEADLESS,
        disable_security=BROWSER_DISABLE_SECURITY,
        args=BROWSER_ARGS,
        is_local=True,
        use_cloud=False,
        enable_default_extensions=False,
        wait_for_network_idle_page_load_time=5.0,
        maximum_wait_page_load_time=30.0,
        wait_between_actions=1.0,
    )
    return browser_profile


async def collect_elements(
    page,
    selectors: list[str] | None,
    prompt_description: str | None,
) -> tuple[dict, dict, list[str]]:

    elements_data: dict[str, list[dict]] = {}
    selector_stats: dict[str, int] = {}

    if prompt_description:
        llm = create_llm()
        print(f"Ищем элемент по описанию: '{prompt_description}'")
        prompt_element = await _get_element_by_prompt_with_timeout(page, prompt_description, llm)
        if not prompt_element:
            raise ValueError("Не удалось найти элемент по описанию.")

        element_data = await extract_element_data(prompt_element)
        selector_key = element_data.get("tag") or "element"
        elements_data[selector_key] = [element_data]
        selector_stats = {selector_key: 1}
        print(f"По описанию найден элемент тега '{selector_key}'.")
    else:
        normalized_selectors = sanitize_selectors(selectors, DEFAULT_SELECTORS, AVAILABLE_SELECTORS)
        for selector in normalized_selectors:
            elements = await page.get_elements_by_css_selector(selector)
            selector_data: list[dict] = []

            for elem in elements:
                if await elem.get_bounding_box():
                    element_data = await extract_element_data(elem)
                    selector_data.append(element_data)

                    if selector_data:
                        elements_data[selector] = selector_data
                        selector_stats[selector] = len(selector_data)
                        print(f"{selector}: {len(selector_data)}")

    return elements_data, selector_stats


def save_elements_snapshot(elements_data: dict) -> None:
    elements_data_file = os.path.join(os.path.dirname(__file__), "elements_data.json")
    try:
        with open(elements_data_file, "w", encoding="utf-8") as f:
            json.dump(elements_data, f, ensure_ascii=False, indent=2)
        print(f"\nДанные успешно сохранены в файл: {elements_data_file}")
    except Exception as e:
        print(f"\nОшибка при сохранении данных в файл: {e}")


async def build_locators(
    elements_data: dict,
    progress_callback=None,
) -> list[dict]:

    collected_locators: list[dict] = []
    current_index = 0
    

    total_chunks = 0
    for selector, elements in elements_data.items():
        chunks = list(chunk_list(elements, MAX_ELEMENTS_PER_CHUNK))
        total_chunks += len(chunks)
    
    processed_chunks = 0

    for selector, elements in elements_data.items():
        chunks = list(chunk_list(elements, MAX_ELEMENTS_PER_CHUNK))
        for idx, chunk in enumerate(chunks, start=1):
            data_chunk = chunk
            try:
                print(f"\n=== Генерация XPath для '{selector}' (часть {idx}/{len(chunks)}) ===\n")
                
                # Обновляем прогресс
                if progress_callback and total_chunks > 0:
                    progress = 0.5 + (processed_chunks / total_chunks) * 0.2
                    progress_callback(progress, f"Генерация XPath для '{selector}' (часть {idx}/{len(chunks)})")
                
                xpath_response = await generate_xpath_locators_structured(data_chunk)
                print(xpath_response)

                if isinstance(xpath_response, list):
                    locators = xpath_response
                else:
                    locators = extract_locators_from_response(xpath_response)

                for i, locator in enumerate(locators):
                    locator['original_index'] = current_index + i
                
                collected_locators.extend(locators)
                current_index += len(locators)
                
            except Exception as e:
                print(f"\nОшибка при генерации XPath для '{selector}' части {idx}: {e}")
                current_index += len(data_chunk)
            
            processed_chunks += 1

    return collected_locators


async def fix_locators(
    invalid_locators: list[dict],
    elements_data: dict,
    progress_callback=None,
) -> list[dict]:
    if not invalid_locators:
        return []
    
    print(f"\n=== Исправление {len(invalid_locators)} некорректных локаторов ===\n")
    
    flat_elements_data = []
    for selector, elements in elements_data.items():
        flat_elements_data.extend(elements)

    elements_for_fixing = []
    
    for invalid_loc in invalid_locators:
        original_index = invalid_loc.get('original_index')
        
        if original_index is not None and 0 <= original_index < len(flat_elements_data):
            elements_for_fixing.append(flat_elements_data[original_index])
            print(f"Локатор сопоставлен с элементом по индексу {original_index}")
        else:
            elements_for_fixing.append({})
            print(f"Не удалось найти элемент для локатора (индекс: {original_index}), используется пустой элемент")

    invalid_chunks = list(chunk_list(invalid_locators, MAX_ELEMENTS_PER_FIX_CHUNK))
    elements_chunks = list(chunk_list(elements_for_fixing, MAX_ELEMENTS_PER_FIX_CHUNK))
    
    all_fixed_locators = []
    
    try:
        for idx, (invalid_chunk, elements_chunk) in enumerate(zip(invalid_chunks, elements_chunks), start=1):
            print(f"Исправление части {idx}/{len(invalid_chunks)} ({len(invalid_chunk)} локаторов)")
            
            if progress_callback:
                progress = 0.95 + (idx / len(invalid_chunks)) * 0.03 
                progress_callback(progress, f"Исправление локаторов (часть {idx}/{len(invalid_chunks)})")
            
            fixed_chunk = await fix_invalid_xpath_locators(
                invalid_locators=invalid_chunk,
                elements_data=elements_chunk
            )
            
            all_fixed_locators.extend(fixed_chunk)
            print(f"Исправлено в части {idx}: {len(fixed_chunk)} локаторов")
        
        print(f"Всего получено исправленных локаторов: {len(all_fixed_locators)}")

        if len(all_fixed_locators) != len(invalid_locators):
            print(f"Количество исправленных локаторов ({len(all_fixed_locators)}) не соответствует количеству некорректных ({len(invalid_locators)})")
        
        return all_fixed_locators
        
    except Exception as e:
        print(f"Ошибка при исправлении локаторов: {e}")
        return []


async def add_selenide(
    collected_locators: list[dict],
    progress_callback=None,
) -> list[dict]:

    if not collected_locators:
        return collected_locators

    selenide_ready = [
        {"xpath": item.get("xpath", ""), "description": item.get("description", "")}
        for item in collected_locators
        if item.get("xpath")
    ]
    selenide_enriched: list[dict] = []
    s_chunks = list(chunk_list(selenide_ready, MAX_ELEMENTS_PER_CHUNK))

    for idx, chunk in enumerate(s_chunks, start=1):
        try:
            print(f"\n=== Генерация SelenideElement (часть {idx}/{len(s_chunks)}) ===\n")

            if progress_callback and len(s_chunks) > 0:
                progress = 0.7 + (idx / len(s_chunks)) * 0.2 
                progress_callback(progress, f"Генерация SelenideElement (часть {idx}/{len(s_chunks)})")
            
            selenide_response = await _generate_selenide_structured_with_timeout(chunk)
            enriched_chunk = selenide_response if isinstance(selenide_response, list) else []
            print(selenide_response)

            for original, enriched in zip(chunk, enriched_chunk):
                selenide_enriched.append(
                    {
                        "xpath": original.get("xpath", ""),
                        "description": enriched.get("description", original.get("description", "")),
                        "selenide_element": enriched.get("selenide_element"),
                    }
                )
        except Exception as e:
            print(f"\nОшибка при генерации SelenideElement для части {idx}: {e}")
            print("Используем оригинальные данные без Selenide элементов.")
            selenide_enriched.extend(chunk)

    if not selenide_enriched:
        return collected_locators

    updated_locators: list[dict] = []
    for original, enriched in zip(collected_locators, selenide_enriched):
        merged = original.copy()
        merged["description"] = enriched.get("description", merged.get("description", ""))
        if enriched.get("selenide_element"):
            merged["selenide_element"] = enriched["selenide_element"]
        updated_locators.append(merged)

    return updated_locators


def save_results(
    collected_locators: list[dict],
    validated_locators: list[dict],
) -> None:

    if not collected_locators:
        return

    xpath_lines: list[str] = []
    for locator in collected_locators:
        if isinstance(locator, dict):
            xpath_lines.append(locator.get("xpath", ""))
        else:
            xpath_lines.append(locator)

    combined_locators = "\n".join(xpath_lines)
    print("\n=== Итоговые XPath-локаторы ===\n")
    print(combined_locators)

    output_file = os.path.join(os.path.dirname(__file__), "xpath_locators.txt")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(combined_locators)
        print(f"\nИтоговые локаторы сохранены в файл: {output_file}")
    except Exception as e:
        print(f"\nНе удалось сохранить итоговые локаторы в файл: {e}")

    validation_file = os.path.join(os.path.dirname(__file__), "xpath_locators_validated.json")
    try:
        with open(validation_file, "w", encoding="utf-8") as f:
            json.dump(validated_locators, f, ensure_ascii=False, indent=2)
        print(f"\nРезультаты проверки локаторов сохранены в файл: {validation_file}")
    except Exception as e:
        print(f"\nНе удалось сохранить результаты проверки локаторов в файл: {e}")


async def main(
    url: str | None = None,
    selectors: list[str] | None = None,
    prompt_description: str | None = None,
    generate_selenide: bool = False,
    progress_callback=None,
):
    browser_profile = build_browser_profile()

    last_error = None
    RETRIES = 3

    for attempt in range(RETRIES):
        browser_session = BrowserSession(browser_profile=browser_profile)
        try:
            if progress_callback:
                progress_callback(0.1, "Запуск браузера...")
            await browser_session.start()

            target_url = url or DEFAULT_URL
            page = await browser_session.new_page(target_url)
            await asyncio.sleep(10)

            if progress_callback:
                progress_callback(0.2, "Сбор элементов со страницы...")
            elements_data, selector_stats = await collect_elements(
                page=page,
                selectors=selectors,
                prompt_description=prompt_description,
            )

            # save_elements_snapshot(elements_data)

            if progress_callback:
                progress_callback(0.5, "Генерация XPath локаторов...")
            collected_locators = await build_locators(
                elements_data=elements_data,
                progress_callback=progress_callback
            )

            if generate_selenide:
                if progress_callback:
                    progress_callback(0.7, "Генерация Selenide элементов...")
                collected_locators = await add_selenide(
                    collected_locators=collected_locators,
                    progress_callback=progress_callback
                )

            if progress_callback:
                progress_callback(0.9, "Валидация локаторов...")
            validated_locators = await validate_locators_on_page(page, collected_locators)
            
            # Разделяем локаторы на корректные и некорректные
            valid_locators, invalid_locators = filter_invalid_locators(validated_locators)
            
            print(f"\nРезультаты валидации:")
            print(f"Корректных локаторов: {len(valid_locators)}")
            print(f"Некорректных локаторов: {len(invalid_locators)}")
            
            # Исправляем некорректные локаторы, если они есть
            final_validated_locators = valid_locators.copy() 
            
            if invalid_locators:
                fixed_locators = await fix_locators(
                    invalid_locators=invalid_locators,
                    elements_data=elements_data,
                    progress_callback=progress_callback
                )
                
                # Повторно валидируем исправленные локаторы
                if fixed_locators:
                    if progress_callback:
                        progress_callback(0.98, "Повторная валидация исправленных локаторов...")
                    
                    revalidated_locators = await validate_locators_on_page(page, fixed_locators)
                    valid_fixed, still_invalid = filter_invalid_locators(revalidated_locators)
                    
                    print(f"\nРезультаты повторной валидации:")
                    print(f"Успешно исправлено: {len(valid_fixed)}")
                    print(f"Все еще некорректных: {len(still_invalid)}")
                    
                    # Добавляем только успешно исправленные локаторы
                    final_validated_locators.extend(valid_fixed)
                    
                    # Если остались неисправленные, добавляем их как есть 
                    if still_invalid:
                        print(f"Внимание: {len(still_invalid)} локаторов не удалось исправить")
                        final_validated_locators.extend(still_invalid)
                else:
                    print("Не удалось исправить локаторы")
            
            all_valid_count = len([loc for loc in final_validated_locators if loc.get('exists') and loc.get('count') == 1])
            
            # save_results(collected_locators, final_validated_locators)

            if progress_callback:
                progress_callback(1.0, "Готово!")

            return {
                "locators": final_validated_locators,
                "selector_stats": selector_stats,
                "valid_count": all_valid_count,
                "total_count": len(final_validated_locators),
            }

        except Exception as e:
            last_error = e
            msg = str(e)
            if ("Document needs to be requested first" in msg) or ("element_highlight_index" in msg):
                print(f"Ошибка '{msg}'. Ретрай {attempt+1}/{RETRIES}")
                continue
            raise
        finally:
            try:
                await browser_session.stop()
            except Exception:
                pass

    if last_error:
        raise last_error


def run_el_attr_workflow(
    url: str | None = None,
    selectors: list[str] | None = None,
    prompt_description: str | None = None,
    generate_selenide: bool = False,
    progress_callback=None,
):
    sanitized = sanitize_selectors(selectors, DEFAULT_SELECTORS, AVAILABLE_SELECTORS) if prompt_description is None else selectors
    return asyncio.run(main(url, sanitized, prompt_description, generate_selenide, progress_callback))


