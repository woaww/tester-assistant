"""
Сервис сохранения результатов генерации локаторов в PostgreSQL.
Использует синхронный psycopg2 для надёжности — без async/asyncpg конфликтов.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2.extras

from src.database.models import ChangeReason, LocatorStage
from src.database.sync_pg import connect_psycopg2

logger = logging.getLogger(__name__)


class LocatorDbService:
    """Сервис сохранения результатов генерации в БД (синхронный psycopg2)."""

    def save_run(
        self,
        url: str,
        run_mode: str,
        locators: List[Dict[str, Any]],
        elements_data: List[Dict[str, Any]],
        llm_config: Optional[Dict] = None,
        auth_config: Optional[Dict] = None,
        metrics: Optional[Dict] = None,
        timings: Optional[Dict] = None,
        artifacts_path: Optional[str] = None,
        project_name: Optional[str] = None,
        project_id: Optional[int] = None,
    ) -> int:
        """Сохранить полный результат генерации в БД."""
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # 1. Определяем проект
            if project_id:
                cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
                project = cur.fetchone()
                if not project:
                    project = self._get_or_create_project(cur, project_name or "Default", url)
                    logger.debug("DB: создан проект %s", project["name"])
            else:
                project = self._get_or_create_project(cur, project_name or "Default", url)
                logger.debug("DB: проект %s id=%s", project["name"], project["id"])

            # 2. Находим или создаём страницу
            cur.execute(
                "SELECT * FROM pages WHERE project_id = %s AND url = %s",
                (project["id"], url),
            )
            page = cur.fetchone()
            if not page:
                cur.execute(
                    "INSERT INTO pages (project_id, url, last_scraped_at) VALUES (%s, %s, %s) RETURNING *",
                    (project["id"], url, datetime.utcnow()),
                )
                page = cur.fetchone()
                logger.debug("DB: создана страница id=%s", page["id"])
            else:
                logger.debug("DB: страница id=%s", page["id"])

            # 3. Создаём запуск
            mode_map = {
                "by_selectors": "BY_SELECTORS",
                "by_tags": "BY_SELECTORS",
                "by_description": "BY_DESCRIPTION",
                "by_parent": "BY_PARENT",
            }
            cur.execute(
                """INSERT INTO locator_runs 
                   (page_id, run_mode, llm_config, auth_config, metrics, timings, artifacts_path,
                    total_elements, valid_locators, invalid_locators, fixed_locators)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 0, 0, 0) RETURNING id""",
                (
                    page["id"],
                    mode_map.get(run_mode, "BY_SELECTORS"),
                    psycopg2.extras.Json(llm_config) if llm_config else None,
                    psycopg2.extras.Json(auth_config) if auth_config else None,
                    psycopg2.extras.Json(metrics) if metrics else None,
                    psycopg2.extras.Json(timings) if timings else None,
                    artifacts_path,
                ),
            )
            run = cur.fetchone()
            run_id = run["id"]

            # 4. Сохраняем элементы
            element_id_map = self._save_elements(cur, run_id, elements_data)

            # 5. Получаем предыдущий запуск для версионирования
            prev_locators = {}
            cur.execute(
                """SELECT id FROM locator_runs 
                   WHERE page_id = %s AND id != %s 
                   ORDER BY created_at DESC LIMIT 1""",
                (page["id"], run_id),
            )
            prev_run = cur.fetchone()
            if prev_run:
                prev_locators = self._get_run_locators_map(cur, prev_run["id"])

            # 6. Сохраняем локаторы с версионированием
            self._save_locators(cur, run_id, locators, element_id_map, elements_data, prev_locators)

            # 7. Обновляем статистику запуска
            self._update_run_stats(cur, run_id, locators)

            conn.commit()
            logger.info(
                "DB: запуск сохранён run_id=%s url=%s locators=%s elements=%s",
                run_id,
                url,
                len(locators),
                len(elements_data),
            )
            return run_id

        except Exception as e:
            conn.rollback()
            logger.exception("DB: откат при сохранении запуска: %s", e)
            raise
        finally:
            conn.close()

    def _get_or_create_project(self, cur, name: str, url: str):
        """Найти или создать проект."""
        cur.execute("SELECT * FROM projects WHERE name = %s", (name,))
        project = cur.fetchone()
        if project:
            return project
        base_url = url.split("/")[0] + "//" + url.split("/")[2] if "/" in url and len(url.split("/")) > 2 else url
        cur.execute(
            "INSERT INTO projects (name, base_url) VALUES (%s, %s) RETURNING *",
            (name, base_url),
        )
        return cur.fetchone()

    def _save_elements(self, cur, run_id: int, elements_data: List[Dict]) -> Dict[int, int]:
        """Сохранить DOM-элементы. Returns: {index -> element_id}."""
        element_id_map = {}
        for idx, el in enumerate(elements_data):
            text_raw = el.get("textContent")
            if isinstance(text_raw, dict):
                text_content = text_raw.get("containsText")
                own_text = text_raw.get("ownText")
            else:
                text_content = text_raw
                own_text = el.get("ownText") or el.get("own_text")

            attrs = el.get("attributes", {})
            if isinstance(attrs, dict):
                pass
            else:
                attrs = {}

            cur.execute(
                """INSERT INTO elements 
                   (run_id, tag, attributes, text_content, own_text, parent_info, siblings, bbox, css_path)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    run_id,
                    el.get("tag") or "unknown",
                    psycopg2.extras.Json(attrs),
                    text_content,
                    own_text,
                    psycopg2.extras.Json(el.get("parent")) if el.get("parent") else None,
                    psycopg2.extras.Json(el.get("siblings")) if el.get("siblings") else None,
                    psycopg2.extras.Json(el.get("bbox")) if el.get("bbox") else None,
                    el.get("cssSelector") or el.get("css_path"),
                ),
            )
            element_id_map[idx] = cur.fetchone()["id"]
        return element_id_map

    def _element_signature(self, el: Dict) -> str:
        """
        Создать подпись элемента на основе DOM-данных для сопоставления.
        Использует tag, class, id, type, ownText, parent tag+text.
        """
        attrs = el.get("attributes", {}) or {}
        text_raw = el.get("textContent", {}) or {}
        own_text = text_raw.get("ownText", "") or text_raw.get("containsText", "") or ""
        parent = el.get("parent") or {}
        parent_attrs = parent.get("attributes", {}) if isinstance(parent, dict) else {}
        parent_text_raw = parent.get("textContent", {}) if isinstance(parent, dict) else {}
        parent_text = parent_text_raw.get("containsText", "") or parent_text_raw.get("ownText", "") or "" if isinstance(parent_text_raw, dict) else ""

        # Берём только stable атрибуты
        sig_parts = [
            el.get("tag", "unknown"),
            attrs.get("id", ""),
            attrs.get("type", ""),
            attrs.get("name", ""),
            attrs.get("role", ""),
            own_text.strip()[:80],
            parent.get("tag", ""),
            parent_text.strip()[:60],
        ]
        return "|".join(str(p) for p in sig_parts)

    def _get_run_locators_map(self, cur, run_id: int) -> Dict[str, dict]:
        """
        Получить локаторы предыдущего запуска в виде dict{dom_signature -> locator}.
        Загружаем элементы через element_snapshot_id и строим подписи.
        """
        cur.execute("""
            SELECT l.*, e.id as elem_id, e.tag, e.attributes, e.text_content, e.own_text,
                   e.parent_info, e.siblings
            FROM locators l
            LEFT JOIN elements e ON e.id = l.element_snapshot_id
            WHERE l.run_id = %s
        """, (run_id,))
        result = {}
        for row in cur.fetchall():
            row = dict(row)
            el_data = {
                "tag": row.get("tag"),
                "attributes": row.get("attributes") or {},
                "textContent": {"ownText": row.get("own_text"), "containsText": row.get("text_content")},
                "parent": row.get("parent_info") or {},
                "siblings": row.get("siblings") or {},
            }
            sig = self._element_signature(el_data)
            if sig:
                result[sig] = row
            # ВСЕГДА индексируем по описанию как фоллбэк
            if row.get("description"):
                result["_desc:" + row["description"]] = row
        return result

    def _save_locators(self, cur, run_id: int, locators: List[Dict], element_id_map, elements_data, prev_locators: Dict[str, dict]):
        """
        Умное версионирование: сопоставление по DOM-подписи элемента (с фоллбэком на description).
        - old valid + new valid → ПРОПУСКАЕМ
        - old invalid + new valid → ОБНОВЛЯЕМ + history
        - оба invalid → ОБНОВЛЯЕМ + history
        - old valid + new invalid → ПРОПУСКАЕМ
        - новый элемент → INSERT
        """
        for loc in locators:
            if not loc.get("xpath"):
                continue

            original_idx = loc.get("original_index")
            element_snapshot_id = element_id_map.get(original_idx) if isinstance(original_idx, int) else None
            stage_str = loc.get("stage", "generated")
            stage = "FIXED" if stage_str == "fixed" else "GENERATED"
            validation = loc.get("validation", {})
            exists = bool(validation.get("exists", loc.get("exists", False)))
            count = int(validation.get("count", loc.get("count", 0)))
            is_valid = (count == 1)
            new_xpath = loc.get("xpath", "")
            selenide_element = loc.get("selenide_element")
            description = loc.get("description", "")

            # Подпись текущего элемента из DOM-данных
            el_data = elements_data[original_idx] if isinstance(original_idx, int) and original_idx < len(elements_data) else {}
            sig = self._element_signature(el_data)

            # 1. Ищем по DOM-подписи
            existing = prev_locators.get(sig) if sig else None
            # 2. Фоллбэк: если не нашли по подписи, ищем по описанию
            if not existing and description:
                existing = prev_locators.get("_desc:" + description)

            old_is_valid = existing and existing.get("is_valid", False) if existing else False

            if existing:
                old_xpath = existing["xpath"]
                # Оба валидны или старый валид+новый невалидн → пропускаем
                if (old_is_valid and is_valid) or (old_is_valid and not is_valid):
                    continue

                # Заменяем
                cur.execute(
                    """UPDATE locators SET xpath=%s, version=version+1, stage=%s,
                       validation=%s, is_valid=%s, selenide_element=%s,
                       element_snapshot_id=%s, run_id=%s, description=%s WHERE id=%s""",
                    (new_xpath, stage, psycopg2.extras.Json({"exists": exists, "count": count}),
                     is_valid, selenide_element, element_snapshot_id, run_id, description, existing["id"]),
                )
                reason_msg = "Заменён: старый невалидный → новый валидный" if (not old_is_valid and is_valid) else "Оба невалидны, обновлён XPath"
                cur.execute(
                    """INSERT INTO locator_history
                       (locator_id, old_xpath, new_xpath, change_reason, change_description, run_id)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (existing["id"], old_xpath, new_xpath, "RE_GENERATION",
                     f"{reason_msg} (run #{run_id})", run_id),
                )
            else:
                # Новый элемент — создаём
                cur.execute(
                    """INSERT INTO locators
                       (run_id, element_snapshot_id, xpath, description, stage, validation, selenide_element, is_valid, version)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1) RETURNING id""",
                    (run_id, element_snapshot_id, new_xpath, description, stage,
                     psycopg2.extras.Json({"exists": exists, "count": count}),
                     selenide_element, is_valid),
                )
                locator_id = cur.fetchone()["id"]
                if stage == "FIXED":
                    cur.execute(
                        """INSERT INTO locator_history
                           (locator_id, old_xpath, new_xpath, change_reason, change_description, run_id)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (locator_id, None, new_xpath, "AUTO_FIX",
                         "Локатор исправлен при первичной генерации", run_id),
                    )

    def _update_run_stats(self, cur, run_id: int, locators: List[Dict]):
        """Обновить статистику запуска."""
        total = len(locators)
        valid = sum(1 for l in locators if l.get("validation", {}).get("count", l.get("count", 0)) == 1)
        invalid = total - valid
        fixed = sum(1 for l in locators if l.get("stage") == "fixed")
        cur.execute(
            """UPDATE locator_runs SET total_elements=%s, valid_locators=%s, 
               invalid_locators=%s, fixed_locators=%s WHERE id=%s""",
            (total, valid, invalid, fixed, run_id),
        )

    async def close(self):
        pass
