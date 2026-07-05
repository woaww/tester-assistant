import json
import logging
import re
from typing import Any

_log = logging.getLogger(__name__)


def chunk_list(items, chunk_size):
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


def sanitize_selectors(selectors, default_selectors, allowed_selectors):
    if not selectors:
        return default_selectors.copy()
    filtered = [s for s in selectors if s in allowed_selectors]
    return filtered if filtered else default_selectors.copy()


def extract_locators_from_response(response_text: str):
    locators = []

    data = None
    try:
        data = json.loads(response_text.strip())
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", response_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

    def append_item(idx: int, xpath: str, description: str, s_line: str | None):
        locators.append(
            {
                "xpath": xpath,
                "description": description or "",
                "selenide_element": s_line,
            }
        )

    if isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, dict) and "xpath" in item:
                append_item(
                    idx,
                    item["xpath"],
                    item.get("description", ""),
                    item.get("selenide_element"),
                )
        return locators

    for idx, raw_line in enumerate(response_text.splitlines()):
        line = raw_line.strip()
        if line and not line.startswith("```") and line.startswith(("//", ".//", "(/", "(.")):
            append_item(idx, line, "", None)

    return locators


async def validate_locators_on_page(page: Any, locators: list[dict | str]) -> list[dict]:
    validated = []
    if not locators:
        return validated

    for locator_item in locators:
        if isinstance(locator_item, str):
            xpath = locator_item
            description = ""
            selenide_element = None
            base: dict[str, Any] = {}
        else:
            xpath = locator_item.get("xpath", "")
            description = locator_item.get("description", "")
            selenide_element = locator_item.get("selenide_element")
            # сохраняем дополнительные поля (stage, original_index, etc.)
            base = dict(locator_item)

        if not xpath:
            continue

        exists = False
        count = 0
        try:
            result = await page.evaluate(
                """
                (xpath) => {
                    try {
                        const snapshot = document.evaluate(
                            xpath,
                            document,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null
                        );
                        return snapshot.snapshotLength;
                    } catch (e) {
                        return 0;
                    }
                }
                """,
                xpath,
            )
            count = int(result) if result else 0
            exists = count > 0
        except Exception as e:
            _log.debug("Проверка XPath '%s': %s", xpath, e)
            count = 0
            exists = False

        validated_item = base
        validated_item["xpath"] = xpath
        validated_item["exists"] = bool(exists)
        validated_item["count"] = count
        if description:
            validated_item["description"] = description
        if selenide_element:
            validated_item["selenide_element"] = selenide_element

        validated.append(validated_item)

        _log.debug(
            "XPath %s: count=%s exists=%s",
            xpath[:80] + ("…" if len(xpath) > 80 else ""),
            count,
            exists,
        )

    return validated


def filter_invalid_locators(validated_locators: list[dict]) -> tuple[list[dict], list[dict]]:
    valid_locators = []
    invalid_locators = []
    
    for locator in validated_locators:
        count = locator.get("count", 0)
        exists = locator.get("exists", False)
        
        # Корректный локатор: существует и находит ровно 1 элемент
        if exists and count == 1:
            valid_locators.append(locator)
        else:
            # Некорректный: не найден (count=0) или находит больше 1 элемента (count>1)
            invalid_locators.append(locator)
    
    return valid_locators, invalid_locators



