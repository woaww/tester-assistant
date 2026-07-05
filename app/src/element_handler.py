import asyncio
import json
from src.browser_config import create_llm, MAX_CHILDREN_ELEMENTS, MAX_TOTAL_ELEMENTS
from src.locator_utils import sanitize_selectors


def try_parse_json(value):
    """Пытается распарсить JSON, возвращает исходное значение при ошибке."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


async def extract_parent(elem):
    """Извлекает данные родительского элемента."""
    return await elem.evaluate(
        """
        () => {
            const parent = this.parentElement;
            if (!parent) return null;

            const usefulAttrs = ['id', 'class', 'name', 'type', 'role', 
                                 'data-testid', 'data-test', 'aria-label', 
                                 'aria-describedby', 'placeholder', 'title', 
                                 'alt', 'href', 'for', 'value'];
            const attrs = {};
            for (const a of parent.attributes) {
                if (usefulAttrs.includes(a.name) || a.name.startsWith('data-')) {
                    attrs[a.name] = a.value;
                }
            }

            const ownTextNodes = Array.from(parent.childNodes)
                .filter(node => node.nodeType === Node.TEXT_NODE)
                .map(node => node.textContent)
                .join('');

            return {
                tag: parent.tagName.toLowerCase(),
                attributes: attrs,
                textContent: {
                    ownText: ownTextNodes || null,
                    containsText: parent.textContent || null
                }
            };
        }
        """
    )


async def get_siblings(elem):
    """Извлекает данные соседних элементов."""
    return await elem.evaluate(
        """
        () => {
            const usefulAttrs = ['id', 'class', 'name', 'type', 'role', 
                                 'data-testid', 'data-test', 'aria-label', 
                                 'aria-describedby', 'placeholder', 'title', 
                                 'alt', 'href', 'for', 'value'];
            
            const collect = el => {
                if (!el) return null;

                const attrs = {};
                for (const a of el.attributes) {
                    if (usefulAttrs.includes(a.name) || a.name.startsWith('data-')) {
                        attrs[a.name] = a.value;
                    }
                }

                const ownTextNodes = Array.from(el.childNodes)
                    .filter(node => node.nodeType === Node.TEXT_NODE)
                    .map(node => node.textContent)
                    .join('');

                return {
                    tag: el.tagName.toLowerCase(),
                    textContent: {
                        ownText: ownTextNodes || null,
                        containsText: el.textContent || null
                    },
                    attributes: attrs
                };
            };

            return { 
                prev: collect(this.previousElementSibling), 
                next: collect(this.nextElementSibling) 
            };
        }
        """
    )


async def extract_element_data(elem):
    """
    Извлекает полные данные об элементе: атрибуты, текст, родитель, соседи.
    """
    data = {}

    # Базовая информация
    basic_info = await elem.get_basic_info()
    data["tag"] = basic_info.get("nodeName", "").lower()
    data["attributes"] = basic_info.get("attributes", {})

    # Текстовое содержимое
    text_data = await elem.evaluate(
        """() => {
            const ownTextNodes = Array.from(this.childNodes)
                .filter(node => node.nodeType === Node.TEXT_NODE)
                .map(node => node.textContent)
                .join('');

            const fullText = this.textContent || null;

            return {
                ownText: ownTextNodes || null,
                containsText: fullText
            };
        }"""
    )
    data["textContent"] = try_parse_json(text_data)

    # Родительский элемент
    parent = await extract_parent(elem)
    data["parent"] = try_parse_json(parent)

    # Соседние элементы
    siblings = await get_siblings(elem)
    data["siblings"] = try_parse_json(siblings)

    return data


async def collect_elements_by_selectors(
    page,
    selectors: list[str],
    *,
    max_total_elements: int = MAX_TOTAL_ELEMENTS,
) -> tuple[dict, dict]:
    """Собирает элементы по CSS селекторам."""
    elements_data = {}
    selector_stats = {}
    collected_total = 0
    
    for selector in selectors:
        elements = await page.get_elements_by_css_selector(selector)
        selector_data = []

        for elem in elements:
            if collected_total >= max_total_elements:
                break
            if await elem.get_bounding_box():
                element_data = await extract_element_data(elem)
                selector_data.append(element_data)
                collected_total += 1

        if selector_data:
            elements_data[selector] = selector_data
            selector_stats[selector] = len(selector_data)
        if collected_total >= max_total_elements:
            break

    return elements_data, selector_stats


async def collect_element_by_description(page, description: str) -> tuple[dict, dict]:
    """Собирает элемент по текстовому описанию."""
    # browser_use иногда возвращает пустую строку/битый JSON при tool-calling,
    # из-за чего падает pydantic (Invalid JSON: EOF). Ретраим этот кейс.
    llm = create_llm()
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            element = await asyncio.wait_for(
                page.get_element_by_prompt(description, llm=llm),
                timeout=90.0,
            )
            last_err = None
            break
        except asyncio.TimeoutError as e:
            last_err = e
            # нет смысла ретраить бесконечно — пользователь увидит таймаут
        except Exception as e:
            # Ловим pydantic/json ошибки (например: "Invalid JSON: EOF ... input_value=''")
            last_err = e
            msg = str(e)
            if ("Invalid JSON" in msg) or ("json_invalid" in msg) or ("ElementResponse" in msg):
                await asyncio.sleep(1.0 + attempt)
                llm = create_llm()
                continue
            raise

    if last_err:
        if isinstance(last_err, asyncio.TimeoutError):
            raise TimeoutError("Не удалось найти элемент по описанию за 90 сек.")
        raise last_err
    
    if not element:
        raise ValueError("Не удалось найти элемент по описанию.")

    element_data = await extract_element_data(element)
    selector_key = element_data.get("tag") or "element"
    
    elements_data = {selector_key: [element_data]}
    selector_stats = {selector_key: 1}
    
    return elements_data, selector_stats


async def collect_children_elements(
    page,
    parent_xpath: str,
    *,
    max_children_elements: int = MAX_CHILDREN_ELEMENTS,
    max_total_elements: int = MAX_TOTAL_ELEMENTS,
) -> tuple[dict, dict]:
    """Собирает дочерние элементы от родительского XPath."""
    # Проверяем существование родительского элемента
    parent_exists = await page.evaluate(
        """
        (xpath) => {
            try {
                const result = document.evaluate(
                    xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                );
                return result.singleNodeValue !== null;
            } catch (e) {
                return false;
            }
        }
        """,
        parent_xpath
    )
    
    if not parent_exists:
        raise ValueError(f"Родительский элемент не найден по XPath: {parent_xpath}")
    
    # Извлекаем дочерние элементы
    children_data_raw = await page.evaluate(_get_children_script(), parent_xpath)
    
    # Парсим результат
    result_data = json.loads(children_data_raw) if isinstance(children_data_raw, str) else children_data_raw
    
    if result_data.get('error'):
        raise ValueError(f"Ошибка при извлечении дочерних элементов: {result_data.get('error')}")
    
    all_children_data = result_data.get('children', [])
    children_count = result_data.get('count', 0)
    
    if children_count == 0:
        raise ValueError("У родительского элемента нет дочерних элементов")
    
    # Ограничиваем количество обрабатываемых элементов
    # Ограничиваем количество обрабатываемых элементов
    children_to_process = all_children_data[:max_children_elements]
    
    # Группируем по тегам и фильтруем только видимые
    children_by_tag = {}
    processed_count = 0
    
    for child_data in children_to_process:
        if processed_count >= max_total_elements:
            break
        if not child_data.get('isVisible', False):
            continue
        
        tag = child_data['tag']
        child_data.pop('isVisible', None)
        
        if tag not in children_by_tag:
            children_by_tag[tag] = []
        
        children_by_tag[tag].append(child_data)
        processed_count += 1
    
    if not children_by_tag:
        raise ValueError("Не удалось извлечь видимые дочерние элементы")
    
    # Формируем результат
    elements_data = {}
    selector_stats = {}
    
    for tag, elements in children_by_tag.items():
        elements_data[tag] = elements
        selector_stats[tag] = len(elements)
    
    return elements_data, selector_stats


def _get_children_script() -> str:
    """Возвращает JavaScript для извлечения дочерних элементов."""
    return """
    (xpath) => {
        try {
            const parent = document.evaluate(
                xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
            ).singleNodeValue;
            
            if (!parent) return JSON.stringify({ 
                error: 'Parent not found', count: 0, tags: {}, children: [] 
            });
            
            const usefulAttrs = ['id', 'class', 'name', 'type', 'role', 
                                 'data-testid', 'data-test', 'aria-label', 
                                 'aria-describedby', 'placeholder', 'title', 
                                 'alt', 'href', 'for', 'value'];
            
            const extractElementData = (elem) => {
                // Атрибуты
                const attrs = {};
                for (const a of elem.attributes) {
                    if (usefulAttrs.includes(a.name) || a.name.startsWith('data-')) {
                        attrs[a.name] = a.value;
                    }
                }
                
                // Текст
                const ownTextNodes = Array.from(elem.childNodes)
                    .filter(node => node.nodeType === Node.TEXT_NODE)
                    .map(node => node.textContent)
                    .join('');
                
                // Родитель
                let parentData = null;
                if (elem.parentElement) {
                    const parentAttrs = {};
                    for (const a of elem.parentElement.attributes) {
                        if (usefulAttrs.includes(a.name) || a.name.startsWith('data-')) {
                            parentAttrs[a.name] = a.value;
                        }
                    }
                    const parentOwnText = Array.from(elem.parentElement.childNodes)
                        .filter(node => node.nodeType === Node.TEXT_NODE)
                        .map(node => node.textContent)
                        .join('');
                    
                    parentData = {
                        tag: elem.parentElement.tagName.toLowerCase(),
                        attributes: parentAttrs,
                        textContent: {
                            ownText: parentOwnText || null,
                            containsText: elem.parentElement.textContent || null
                        }
                    };
                }
                
                // Соседи
                const extractSibling = (sibling) => {
                    if (!sibling) return null;
                    const sibAttrs = {};
                    for (const a of sibling.attributes) {
                        if (usefulAttrs.includes(a.name) || a.name.startsWith('data-')) {
                            sibAttrs[a.name] = a.value;
                        }
                    }
                    const sibOwnText = Array.from(sibling.childNodes)
                        .filter(node => node.nodeType === Node.TEXT_NODE)
                        .map(node => node.textContent)
                        .join('');
                    
                    return {
                        tag: sibling.tagName.toLowerCase(),
                        textContent: {
                            ownText: sibOwnText || null,
                            containsText: sibling.textContent || null
                        },
                        attributes: sibAttrs
                    };
                };
                
                return {
                    tag: elem.tagName.toLowerCase(),
                    attributes: attrs,
                    textContent: {
                        ownText: ownTextNodes || null,
                        containsText: elem.textContent || null
                    },
                    parent: parentData,
                    siblings: {
                        prev: extractSibling(elem.previousElementSibling),
                        next: extractSibling(elem.nextElementSibling)
                    },
                    isVisible: elem.offsetParent !== null
                };
            };
            
            // Получаем ВСЕХ потомков
            const allDescendants = parent.querySelectorAll('*');
            const children = [];
            const tags = {};
            
            for (let child of allDescendants) {
                const childData = extractElementData(child);
                children.push(childData);
                
                const tag = childData.tag;
                tags[tag] = (tags[tag] || 0) + 1;
            }
            
            return JSON.stringify({ 
                count: allDescendants.length,
                tags: tags,
                parentTag: parent.tagName.toLowerCase(),
                parentClass: parent.className,
                children: children
            });
        } catch (e) {
            return JSON.stringify({ 
                error: e.toString(), count: 0, tags: {}, children: [] 
            });
        }
    }
    """


async def collect_elements(
    page,
    selectors: list[str] = None,
    prompt_description: str = None,
    parent_xpath: str = None,
    available_selectors: list[str] = None,
    default_selectors: list[str] = None,
    max_total_elements: int = MAX_TOTAL_ELEMENTS,
    max_children_elements: int = MAX_CHILDREN_ELEMENTS,
) -> tuple[dict, dict]:
    """
    Универсальная функция для сбора элементов в зависимости от режима.
    """
    # Режим дочерних элементов
    if parent_xpath:
        return await collect_children_elements(
            page,
            parent_xpath,
            max_children_elements=max_children_elements,
            max_total_elements=max_total_elements,
        )
    
    # Режим поиска по описанию
    elif prompt_description:
        return await collect_element_by_description(page, prompt_description)
    
    # Режим по CSS-селекторам
    else:
        normalized_selectors = sanitize_selectors(
            selectors, default_selectors, available_selectors
        )
        return await collect_elements_by_selectors(
            page,
            normalized_selectors,
            max_total_elements=max_total_elements,
        )