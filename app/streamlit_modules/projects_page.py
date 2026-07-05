"""Страница управления проектами — создание, редактирование, удаление."""

import concurrent.futures

import streamlit as st

from streamlit_modules.async_bridge import run_async
from streamlit_modules.ui import section_label
from src.database.sync_pg import connect_psycopg2


def projects_page():
    if "projects_initialized" not in st.session_state:
        st.session_state["projects_initialized"] = True
        st.session_state.pop("editing_project_id", None)

    if st.button("+ Новый проект", type="primary"):
        st.session_state.pop("editing_project_id", None)
        st.session_state["show_project_form"] = True

    if st.session_state.get("show_project_form"):
        _show_project_form()

    projects = _load_projects()
    if not projects:
        return

    st.divider()
    section_label(f"{len(projects)} проектов")

    for proj in projects:
        with st.expander(
            f"{proj['name']}  —  {proj.get('base_url') or 'URL не указан'}",
            expanded=False,
        ):
            if proj.get("description"):
                st.caption(proj["description"])

            col_info1, col_info2, col_info3 = st.columns(3)
            col_info1.metric("Страниц", proj.get("pages_count", 0))
            col_info2.metric("Запусков", proj.get("runs_count", 0))
            if proj.get("last_run_at"):
                col_info3.caption(f"Последний запуск:\n{proj['last_run_at']}")

            col_actions = st.columns([1, 1, 4])
            with col_actions[0]:
                if st.button("Изменить", key=f"edit_{proj['id']}", width="stretch"):
                    st.session_state["editing_project_id"] = proj["id"]
                    st.session_state["show_project_form"] = True
                    st.rerun()
            with col_actions[1]:
                if st.button("Удалить", key=f"del_{proj['id']}", type="secondary", width="stretch"):
                    st.session_state["deleting_project_id"] = proj["id"]

            if st.session_state.get("deleting_project_id") == proj["id"]:
                st.warning(f"Удалить проект **{proj['name']}**? Все данные будут удалены безвозвратно.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Да, удалить", key=f"confirm_del_{proj['id']}"):
                        _delete_project(proj["id"])
                        st.session_state.pop("deleting_project_id", None)
                        st.success(f"Проект «{proj['name']}» удалён")
                        st.rerun()
                with c2:
                    if st.button("Отмена", key=f"cancel_del_{proj['id']}"):
                        st.session_state.pop("deleting_project_id", None)
                        st.rerun()


def _show_project_form():
    """Форма создания/редактирования проекта."""
    editing_id = st.session_state.get("editing_project_id")
    project = None

    with st.container(border=True):
        if editing_id:
            project = _get_project(editing_id)
            st.subheader("Редактирование проекта")
        else:
            st.subheader("Создание нового проекта")

        with st.form("project_form"):
            name = st.text_input(
                "Название проекта *",
                value=project.get("name", "") if project else "",
                help="Например: Личный кабинет сотрудника, Портал поставщиков",
            )
            base_url = st.text_input(
                "Базовый URL",
                value=project.get("base_url", "") if project else "",
                help="Основной адрес проекта, например https://example.com",
            )
            description = st.text_area(
                "Описание",
                value=project.get("description", "") if project else "",
                help="Краткое описание проекта для команды",
            )

            submitted = st.form_submit_button("Сохранить", width="stretch", type="primary")
            if submitted:
                if not name or not name.strip():
                    st.error("Название проекта обязательно для заполнения")
                else:
                    if editing_id:
                        _update_project(editing_id, name.strip(), base_url.strip(), description.strip())
                        st.success(f"Проект «{name}» обновлён")
                    else:
                        _create_project(name.strip(), base_url.strip(), description.strip())
                        st.success(f"Проект «{name}» создан")

                    st.session_state.pop("show_project_form", None)
                    st.session_state.pop("editing_project_id", None)
                    st.rerun()

            # Кнопка отмены
            if st.form_submit_button("Отмена", width="stretch"):
                st.session_state.pop("show_project_form", None)
                st.session_state.pop("editing_project_id", None)
                st.rerun()


# ============ DB Helpers ============

def _load_projects() -> list[dict]:
    try:
        from src.database.locator_query_service import LocatorQueryService

        async def _fetch():
            svc = LocatorQueryService()
            try:
                stats = await svc.get_runs_by_project()
            finally:
                await svc.close()
            projects = _get_all_projects()
            stats_map = {s["project_name"]: s for s in stats}
            for p in projects:
                s = stats_map.get(p["name"], {})
                p["pages_count"] = s.get("pages_count", 0)
                p["runs_count"] = s.get("runs_count", 0)
                p["last_run_at"] = s.get("last_run_at")
            return projects

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(lambda: run_async(_fetch())).result(timeout=15)
    except Exception as e:
        st.warning(f"Не удалось загрузить проекты: {e}")
        return []


def _get_all_projects() -> list[dict]:
    import psycopg2.extras

    conn = connect_psycopg2()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, name, base_url, description FROM projects ORDER BY name")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def _get_project(project_id: int) -> dict | None:
    import psycopg2.extras

    conn = connect_psycopg2()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, name, base_url, description FROM projects WHERE id = %s", (project_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _create_project(name: str, base_url: str, description: str):
    conn = connect_psycopg2()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO projects (name, base_url, description) VALUES (%s, %s, %s)",
            (name, base_url or None, description or None),
        )
        conn.commit()
    finally:
        conn.close()


def _update_project(project_id: int, name: str, base_url: str, description: str):
    conn = connect_psycopg2()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE projects SET name = %s, base_url = %s, description = %s WHERE id = %s",
            (name, base_url or None, description or None, project_id),
        )
        conn.commit()
    finally:
        conn.close()


def _delete_project(project_id: int):
    conn = connect_psycopg2()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        conn.commit()
    finally:
        conn.close()


def get_project_list_for_selector() -> list[str]:
    """Получить список имён проектов для селектора. Синхронная функция."""
    try:
        import psycopg2.extras
        conn = connect_psycopg2()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT id, name FROM projects ORDER BY name")
            return [f"{r['id']}|{r['name']}" for r in cur.fetchall()]
        finally:
            conn.close()
    except Exception:
        return []


def get_project_id_from_selection(selection: str) -> int | None:
    """Получить ID проекта из селектора."""
    if selection and "|" in selection:
        return int(selection.split("|")[0])
    return None
