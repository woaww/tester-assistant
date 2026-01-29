import asyncio
from src.browser_config import MAX_ELEMENTS_PER_CHUNK, MAX_ELEMENTS_PER_FIX_CHUNK
from src.locator_utils import chunk_list, extract_locators_from_response, validate_locators_on_page, filter_invalid_locators
from generate_modules.xpath_generator import (
    generate_xpath_locators_structured,
    generate_selenide_elements_structured,
    fix_invalid_xpath_locators,
)


async def build_locators(elements_data: dict, progress_callback=None) -> list[dict]:
    """
    Генерирует XPath локаторы для собранных элементов.
    """
    collected_locators = []
    current_index = 0
    
    # Подсчитываем общее количество чанков
    total_chunks = sum(
        len(list(chunk_list(elements, MAX_ELEMENTS_PER_CHUNK)))
        for elements in elements_data.values()
    )
    
    processed_chunks = 0

    for selector, elements in elements_data.items():
        chunks = list(chunk_list(elements, MAX_ELEMENTS_PER_CHUNK))
        
        for idx, chunk in enumerate(chunks, start=1):
            try:
                # Обновляем прогресс
                if progress_callback and total_chunks > 0:
                    progress = 0.5 + (processed_chunks / total_chunks) * 0.2
                    progress_callback(progress, f"Генерация XPath для '{selector}' (часть {idx}/{len(chunks)})")
                
                # Генерируем локаторы
                xpath_response = await generate_xpath_locators_structured(chunk)
                
                locators = (xpath_response if isinstance(xpath_response, list) 
                           else extract_locators_from_response(xpath_response))

                # Индексы для отслеживания соответствия
                for i, locator in enumerate(locators):
                    locator['original_index'] = current_index + i
                
                collected_locators.extend(locators)
                current_index += len(locators)
                
            except Exception as e:
                print(f"Ошибка при генерации XPath для '{selector}' части {idx}: {e}")
                current_index += len(chunk)
            
            processed_chunks += 1

    return collected_locators


async def fix_invalid_locators_internal(
    invalid_locators: list[dict],
    elements_data: dict,
    progress_callback=None,
) -> list[dict]:
    """
    Исправляет некорректные локаторы с помощью LLM.
    """
    if not invalid_locators:
        return []
    
    # Создаем плоский список элементов
    flat_elements_data = []
    for elements in elements_data.values():
        flat_elements_data.extend(elements)

    # Сопоставляем локаторы с элементами
    elements_for_fixing = []
    for invalid_loc in invalid_locators:
        original_index = invalid_loc.get('original_index')
        
        if original_index is not None and 0 <= original_index < len(flat_elements_data):
            elements_for_fixing.append(flat_elements_data[original_index])
        else:
            elements_for_fixing.append({})

    # Разбиваем на чанки для обработки
    invalid_chunks = list(chunk_list(invalid_locators, MAX_ELEMENTS_PER_FIX_CHUNK))
    elements_chunks = list(chunk_list(elements_for_fixing, MAX_ELEMENTS_PER_FIX_CHUNK))
    
    all_fixed_locators = []
    
    try:
        for idx, (invalid_chunk, elements_chunk) in enumerate(zip(invalid_chunks, elements_chunks), start=1):
            if progress_callback:
                progress = 0.95 + (idx / len(invalid_chunks)) * 0.03 
                progress_callback(progress, f"Исправление локаторов (часть {idx}/{len(invalid_chunks)})")
            
            fixed_chunk = await fix_invalid_xpath_locators(
                invalid_locators=invalid_chunk,
                elements_data=elements_chunk
            )
            
            all_fixed_locators.extend(fixed_chunk)
        
        return all_fixed_locators
        
    except Exception as e:
        print(f"Ошибка при исправлении локаторов: {e}")
        return []


async def add_selenide_elements(collected_locators: list[dict], progress_callback=None) -> list[dict]:
    """
    Добавляет Selenide элементы к локаторам.
    """
    if not collected_locators:
        return collected_locators

    # Подготавливаем данные для генерации Selenide
    selenide_ready = [
        {"xpath": item.get("xpath", ""), "description": item.get("description", "")}
        for item in collected_locators
        if item.get("xpath")
    ]
    
    selenide_enriched = []
    s_chunks = list(chunk_list(selenide_ready, MAX_ELEMENTS_PER_CHUNK))

    for idx, chunk in enumerate(s_chunks, start=1):
        try:
            if progress_callback and len(s_chunks) > 0:
                progress = 0.7 + (idx / len(s_chunks)) * 0.2 
                progress_callback(progress, f"Генерация SelenideElement (часть {idx}/{len(s_chunks)})")
            
            selenide_response = await asyncio.wait_for(
                generate_selenide_elements_structured(chunk), 
                timeout=180.0
            )
            
            enriched_chunk = selenide_response if isinstance(selenide_response, list) else []

            for original, enriched in zip(chunk, enriched_chunk):
                selenide_enriched.append({
                    "xpath": original.get("xpath", ""),
                    "description": enriched.get("description", original.get("description", "")),
                    "selenide_element": enriched.get("selenide_element"),
                })
                
        except Exception as e:
            print(f"Ошибка при генерации SelenideElement для части {idx}: {e}")
            selenide_enriched.extend(chunk)

    if not selenide_enriched:
        return collected_locators

    # Объединяем оригинальные локаторы с Selenide элементами
    updated_locators = []
    for original, enriched in zip(collected_locators, selenide_enriched):
        merged = original.copy()
        merged["description"] = enriched.get("description", merged.get("description", ""))
        if enriched.get("selenide_element"):
            merged["selenide_element"] = enriched["selenide_element"]
        updated_locators.append(merged)

    return updated_locators


async def validate_and_fix_locators(
    page,
    collected_locators: list[dict],
    elements_data: dict,
    progress_callback=None
) -> list[dict]:
    """
    Валидирует локаторы и исправляет некорректные.
    """
    if progress_callback:
        progress_callback(0.9, "Валидация локаторов...")
    
    # Валидируем локаторы
    validated_locators = await validate_locators_on_page(page, collected_locators)
    
    # Разделяем на корректные и некорректные
    valid_locators, invalid_locators = filter_invalid_locators(validated_locators)
    
    final_validated_locators = valid_locators.copy()
    
    # Исправляем некорректные локаторы
    if invalid_locators:
        fixed_locators = await fix_invalid_locators_internal(
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
            
            # Добавляем успешно исправленные локаторы
            final_validated_locators.extend(valid_fixed)
            
            # Добавляем неисправленные как есть
            if still_invalid:
                final_validated_locators.extend(still_invalid)
    
    return final_validated_locators