import asyncio
import logging
import time

from src.browser_config import MAX_ELEMENTS_PER_CHUNK, MAX_ELEMENTS_PER_FIX_CHUNK
from src.locator_utils import chunk_list, extract_locators_from_response, validate_locators_on_page, filter_invalid_locators
from generate_modules.xpath_generator import (
    generate_xpath_locators_structured,
    generate_selenide_elements_structured,
    fix_invalid_xpath_locators,
)

_log = logging.getLogger(__name__)


async def build_locators(
    elements_data: dict,
    progress_callback=None,
    *,
    chunk_size: int = MAX_ELEMENTS_PER_CHUNK,
) -> list[dict]:
    """
    Генерирует XPath локаторы для собранных элементов.
    """
    collected_locators = []
    current_index = 0
    
    # Подсчитываем общее количество чанков
    total_chunks = sum(
        len(list(chunk_list(elements, chunk_size)))
        for elements in elements_data.values()
    )
    
    processed_chunks = 0

    for selector, elements in elements_data.items():
        # Проставляем стабильный element_id каждому элементу внутри selector group
        prepared = []
        for idx, el in enumerate(elements):
            if isinstance(el, dict):
                el_copy = dict(el)
                el_copy.setdefault("element_id", f"{selector}::{idx}")
                prepared.append(el_copy)
            else:
                prepared.append({"element_id": f"{selector}::{idx}"})

        chunks = list(chunk_list(prepared, chunk_size))
        
        for idx, chunk in enumerate(chunks, start=1):
            try:
                # Обновляем прогресс
                if progress_callback and total_chunks > 0:
                    progress = 0.5 + (processed_chunks / total_chunks) * 0.2
                    progress_callback(progress, f"Генерация XPath для '{selector}' (часть {idx}/{len(chunks)})")
                
                # Генерируем локаторы
                # ВАЖНО: element_id нужен нам для сопоставления, но не должен попадать в LLM контекст
                element_ids = [c.get("element_id") if isinstance(c, dict) else None for c in chunk]
                llm_chunk = []
                for c in chunk:
                    if isinstance(c, dict):
                        c2 = dict(c)
                        c2.pop("element_id", None)
                        llm_chunk.append(c2)
                    else:
                        llm_chunk.append({})

                locators, raw_meta = await generate_xpath_locators_structured(llm_chunk)
                # сопоставляем element_id по позиции, если модель не вернула явный ключ
                for i, loc in enumerate(locators):
                    if isinstance(loc, dict) and "element_id" not in loc and i < len(element_ids):
                        if element_ids[i]:
                            loc["element_id"] = element_ids[i]
                # сырой ответ LLM на чанк
                for loc in locators:
                    if isinstance(loc, dict):
                        loc.setdefault("_raw_llm_meta", raw_meta)

                # Индексы для отслеживания соответствия
                for i, locator in enumerate(locators):
                    locator['original_index'] = current_index + i
                
                collected_locators.extend(locators)
                current_index += len(locators)
                
            except Exception as e:
                _log.warning("Генерация XPath: селектор=%s чанк=%s: %s", selector, idx, e)
                current_index += len(chunk)
            
            processed_chunks += 1

    return collected_locators


async def fix_invalid_locators_internal(
    invalid_locators: list[dict],
    elements_data: dict,
    progress_callback=None,
    *,
    fix_chunk_size: int = MAX_ELEMENTS_PER_FIX_CHUNK,
) -> list[dict]:
    """
    Исправляет некорректные локаторы с помощью LLM.
    """
    if not invalid_locators:
        return []
    
    # Создаем плоский индекс элементов по element_id
    elements_by_id: dict[str, dict] = {}
    for group, elements in elements_data.items():
        if not isinstance(elements, list):
            continue
        for idx, el in enumerate(elements):
            if not isinstance(el, dict):
                continue
            element_id = el.get("element_id") or f"{group}::{idx}"
            elements_by_id[str(element_id)] = el

    # Сопоставляем локаторы с элементами по element_id (fallback: original_index)
    flat_elements_data: list[dict] = []
    for elements in elements_data.values():
        if isinstance(elements, list):
            flat_elements_data.extend([e for e in elements if isinstance(e, dict)])

    elements_for_fixing = []
    for invalid_loc in invalid_locators:
        element_id = invalid_loc.get("element_id")
        if element_id and str(element_id) in elements_by_id:
            elements_for_fixing.append(elements_by_id[str(element_id)])
            continue
        original_index = invalid_loc.get("original_index")
        if isinstance(original_index, int) and 0 <= original_index < len(flat_elements_data):
            elements_for_fixing.append(flat_elements_data[original_index])
        else:
            elements_for_fixing.append({})

    # Разбиваем на чанки для обработки
    invalid_chunks = list(chunk_list(invalid_locators, fix_chunk_size))
    elements_chunks = list(chunk_list(elements_for_fixing, fix_chunk_size))
    
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
            fixed_chunk, raw_meta = fixed_chunk

            # возвращаем original_index обратно (и другие поля), чтобы не потерять сопоставление
            if isinstance(fixed_chunk, list):
                merged = []
                for src, fixed in zip(invalid_chunk, fixed_chunk):
                    fixed_item = fixed if isinstance(fixed, dict) else {}
                    src_item = src if isinstance(src, dict) else {}
                    fixed_item.setdefault("element_id", src_item.get("element_id"))
                    fixed_item.setdefault("original_index", src_item.get("original_index"))
                    fixed_item.setdefault("selenide_element", src_item.get("selenide_element"))
                    fixed_item.setdefault("_raw_llm_meta", raw_meta)
                    merged.append(fixed_item)
                fixed_chunk = merged
            
            all_fixed_locators.extend(fixed_chunk)
        
        return all_fixed_locators
        
    except Exception as e:
        _log.warning("Исправление локаторов: %s", e)
        return []


async def add_selenide_elements(
    collected_locators: list[dict],
    progress_callback=None,
    *,
    chunk_size: int = MAX_ELEMENTS_PER_CHUNK,
) -> list[dict]:
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
    s_chunks = list(chunk_list(selenide_ready, chunk_size))

    for idx, chunk in enumerate(s_chunks, start=1):
        try:
            if progress_callback and len(s_chunks) > 0:
                progress = 0.7 + (idx / len(s_chunks)) * 0.2 
                progress_callback(progress, f"Генерация SelenideElement (часть {idx}/{len(s_chunks)})")
            
            enriched_chunk, raw_meta = await generate_selenide_elements_structured(chunk)

            for original, enriched in zip(chunk, enriched_chunk):
                selenide_enriched.append({
                    "xpath": original.get("xpath", ""),
                    "description": enriched.get("description", original.get("description", "")),
                    "selenide_element": enriched.get("selenide_element"),
                    "_raw_llm_meta": raw_meta,
                })
                
        except Exception as e:
            _log.warning("SelenideElement чанк %s: %s", idx, e)
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
    progress_callback=None,
    *,
    fix_chunk_size: int = MAX_ELEMENTS_PER_FIX_CHUNK,
) -> tuple[list[dict], dict]:
    """
    Валидирует локаторы и исправляет некорректные.
    """
    timings = {"validate_locators_s": None, "fix_locators_s": None}
    if progress_callback:
        progress_callback(0.9, "Валидация локаторов...")
    
    # Валидируем локаторы
    t0 = time.perf_counter()
    validated_locators = await validate_locators_on_page(page, collected_locators)
    timings["validate_locators_s"] = time.perf_counter() - t0
    for item in validated_locators:
        if isinstance(item, dict):
            item.setdefault("stage", "generated")
    
    # Разделяем на корректные и некорректные
    valid_locators, invalid_locators = filter_invalid_locators(validated_locators)
    
    final_validated_locators = valid_locators.copy()

    stats = {
        "total_after_generation": len(validated_locators),
        "valid_after_generation": len(valid_locators),
        "invalid_after_generation": len(invalid_locators),
        "fixed_valid": 0,
        "still_invalid": 0,
    }
    
    # Исправляем некорректные локаторы
    if invalid_locators:
        t1 = time.perf_counter()
        fixed_locators = await fix_invalid_locators_internal(
            invalid_locators=invalid_locators,
            elements_data=elements_data,
            progress_callback=progress_callback
            ,
            fix_chunk_size=fix_chunk_size,
        )
        # маркируем как fixed до ре-валидации, чтобы stage не потерялся
        for item in fixed_locators or []:
            if isinstance(item, dict):
                item["stage"] = "fixed"
        
        # Повторно валидируем исправленные локаторы
        if fixed_locators:
            if progress_callback:
                progress_callback(0.98, "Повторная валидация исправленных локаторов...")
            
            revalidated_locators = await validate_locators_on_page(page, fixed_locators)
            timings["fix_locators_s"] = time.perf_counter() - t1
            valid_fixed, still_invalid = filter_invalid_locators(revalidated_locators)
            stats["fixed_valid"] = len(valid_fixed)
            stats["still_invalid"] = len(still_invalid)
            
            # Добавляем успешно исправленные локаторы
            final_validated_locators.extend(valid_fixed)
            
            # Добавляем неисправленные как есть
            if still_invalid:
                final_validated_locators.extend(still_invalid)

    # финальные метрики
    total = stats["total_after_generation"] or 0
    invalid0 = stats["invalid_after_generation"] or 0
    valid0 = stats["valid_after_generation"] or 0
    fixed_valid = stats["fixed_valid"] or 0
    stats["accuracy"] = (valid0 / total) if total else None
    stats["fix_rate"] = (fixed_valid / invalid0) if invalid0 else None
    stats["correctness"] = ((valid0 + fixed_valid) / total) if total else None
    stats.update(timings)

    return final_validated_locators, stats