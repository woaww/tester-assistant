"""
Query-сервис для чтения данных из БД.
Использует синхронный psycopg2 для надёжности — без async/asyncpg проблем.
"""

import logging
from typing import Any, Dict, List, Optional

import psycopg2.extras

from src.database.sync_pg import connect_psycopg2

logger = logging.getLogger(__name__)


class LocatorQueryService:
    """Сервис для чтения данных из БД."""

    async def get_runs_history(self, limit: int = 50, offset: int = 0, project_id: Optional[int] = None):
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if project_id:
                cur.execute("""
                    SELECT lr.id as run_id, p.url, pr.name as project_name,
                           lr.run_mode, lr.total_elements, lr.valid_locators,
                           lr.invalid_locators, lr.fixed_locators,
                           lr.metrics, lr.timings, lr.created_at
                    FROM locator_runs lr
                    JOIN pages p ON p.id = lr.page_id
                    JOIN projects pr ON pr.id = p.project_id
                    WHERE pr.id = %s
                    ORDER BY lr.created_at DESC
                    LIMIT %s OFFSET %s
                """, (project_id, limit, offset))
            else:
                cur.execute("""
                    SELECT lr.id as run_id, p.url, pr.name as project_name,
                           lr.run_mode, lr.total_elements, lr.valid_locators,
                           lr.invalid_locators, lr.fixed_locators,
                           lr.metrics, lr.timings, lr.created_at
                    FROM locator_runs lr
                    JOIN pages p ON p.id = lr.page_id
                    JOIN projects pr ON pr.id = p.project_id
                    ORDER BY lr.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    async def get_run_detail(self, run_id: int):
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT lr.*, p.url, pr.name as project_name
                FROM locator_runs lr
                JOIN pages p ON p.id = lr.page_id
                JOIN projects pr ON pr.id = p.project_id
                WHERE lr.id = %s
            """, (run_id,))
            row = cur.fetchone()
            if not row:
                return None
            row_dict = dict(row)

            cur.execute("""
                SELECT id, xpath, description, stage, validation,
                       selenide_element, is_valid, version, created_at
                FROM locators WHERE run_id = %s ORDER BY id
            """, (run_id,))
            locators = [dict(l) for l in cur.fetchall()]

            row_dict["locators"] = locators
            return row_dict
        finally:
            conn.close()

    async def get_dashboard_stats(self):
        conn = connect_psycopg2()
        try:
            cur = conn.cursor()
            result = {}

            cur.execute("SELECT COUNT(*) FROM projects")
            result["projects_count"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM pages")
            result["pages_count"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM locator_runs")
            result["runs_count"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM locators")
            result["locators_count"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM locators WHERE is_valid = true")
            result["valid_locators"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM locators WHERE stage = 'FIXED'")
            result["fixed_locators"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM locator_history")
            result["history_entries"] = cur.fetchone()[0]

            cur.execute("""
                SELECT AVG(CASE WHEN metrics->>'correctness' IS NOT NULL
                           THEN (metrics->>'correctness')::float ELSE NULL END)
                FROM locator_runs
            """)
            avg = cur.fetchone()[0]
            result["avg_correctness"] = round(float(avg), 3) if avg else None

            return result
        finally:
            conn.close()

    async def get_locator_history(self, locator_id: int):
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT lh.id, lh.old_xpath, lh.new_xpath, lh.change_reason,
                       lh.change_description, lh.run_id, lh.changed_at
                FROM locator_history lh
                WHERE lh.locator_id = %s ORDER BY lh.changed_at DESC
            """, (locator_id,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    async def get_locators_for_run(self, run_id: int, only_valid: bool = False):
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            q = """SELECT id, xpath, description, stage, validation,
                          selenide_element, is_valid, version, created_at
                   FROM locators WHERE run_id = %s"""
            if only_valid:
                q += " AND is_valid = true"
            q += " ORDER BY id"
            cur.execute(q, (run_id,))
            return [dict(l) for l in cur.fetchall()]
        finally:
            conn.close()

    async def get_stability_report(self, limit: int = 20):
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT e.tag, e.attributes->>'id' as element_id,
                       e.text_content,
                       COUNT(DISTINCT lh.id) as fix_count,
                       COUNT(DISTINCT l.id) as total_generations
                FROM elements e
                LEFT JOIN locators l ON l.element_snapshot_id = e.id
                LEFT JOIN locator_history lh ON lh.locator_id = l.id
                GROUP BY e.id, e.tag, e.attributes->>'id', e.text_content
                HAVING COUNT(DISTINCT lh.id) > 0
                ORDER BY fix_count DESC LIMIT %s
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    async def get_runs_by_project(self):
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT pr.name as project_name, pr.base_url,
                       COUNT(DISTINCT p.id) as pages_count,
                       COUNT(lr.id) as runs_count,
                       MAX(lr.created_at) as last_run_at
                FROM projects pr
                LEFT JOIN pages p ON p.project_id = pr.id
                LEFT JOIN locator_runs lr ON lr.page_id = p.id
                GROUP BY pr.id, pr.name, pr.base_url
                ORDER BY runs_count DESC
            """)
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    async def close(self):
        pass

    async def get_pages_with_locator(self, project_id=None):
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if project_id:
                cur.execute("""
                    SELECT p.id as page_id, p.url, p.project_id, pr.name as project_name,
                           COUNT(DISTINCT l.id) as locator_count
                    FROM pages p
                    JOIN projects pr ON pr.id = p.project_id
                    LEFT JOIN locator_runs lr ON lr.page_id = p.id
                    LEFT JOIN locators l ON l.run_id = lr.id
                    WHERE pr.id = %s
                    GROUP BY p.id, p.url, p.project_id, pr.name
                    ORDER BY p.url
                """, (project_id,))
            else:
                cur.execute("""
                    SELECT p.id as page_id, p.url, p.project_id, pr.name as project_name,
                           COUNT(DISTINCT l.id) as locator_count
                    FROM pages p
                    JOIN projects pr ON pr.id = p.project_id
                    LEFT JOIN locator_runs lr ON lr.page_id = p.id
                    LEFT JOIN locators l ON l.run_id = lr.id
                    GROUP BY p.id, p.url, p.project_id, pr.name
                    ORDER BY p.url
                """)
            pages = [dict(r) for r in cur.fetchall()]

            for page in pages:
                cur.execute("""
                    SELECT l.id, l.xpath, l.description, l.stage, l.validation,
                           l.selenide_element, l.is_valid, l.version, l.created_at
                    FROM locators l
                    JOIN locator_runs lr ON lr.id = l.run_id
                    WHERE lr.page_id = %s
                    ORDER BY l.description
                """, (page["page_id"],))
                page["locators"] = [dict(l) for l in cur.fetchall()]

            return pages
        finally:
            conn.close()
