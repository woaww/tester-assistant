"""Страница просмотра всех локаторов для каждой страницы."""

import concurrent.futures

import pandas as pd
import streamlit as st

from streamlit_modules.async_bridge import run_async
from streamlit_modules.ui import section_label


def locators_page():
    from streamlit_modules.projects_page import get_project_list_for_selector, get_project_id_from_selection

    project_options = get_project_list_for_selector()
    selected_project_id = None
    if project_options:
        project_labels = ["Все проекты"] + [opt.split("|", 1)[1] for opt in project_options]
        selected_label = st.selectbox(
            "Проект", options=project_labels, index=0, key="locators_project_filter"
        )
        if selected_label != "Все проекты":
            idx = project_labels.index(selected_label)
            selected_project_id = get_project_id_from_selection(project_options[idx - 1])
    else:
        st.info("Нет проектов. Создайте проект на вкладке Проекты.")
        return

    pages_data = _load_pages_with_locators(project_id=selected_project_id)
    if not pages_data:
        st.info("Нет данных. Сгенерируйте локаторы на странице Генератор.")
        return

    section_label(f"{len(pages_data)} страниц")

    for page in pages_data:
        loc_count = len(page["locators"])
        proj_label = f" · {page['project_name']}" if page.get("project_name") else ""
        with st.expander(f"{page['url']}  —  {loc_count} локаторов{proj_label}", expanded=False):
            if not page["locators"]:
                st.caption("Локаторы пока не сгенерированы")
                continue

            f_col1, f_col2 = st.columns(2)
            with f_col1:
                filter_valid = st.selectbox(
                    "Валидность", ["Все", "Валидные", "Невалидные"],
                    key=f"fv_{page['page_id']}",
                    label_visibility="collapsed",
                )
            with f_col2:
                search = st.text_input("Поиск", placeholder="XPath или описание...", key=f"fs_{page['page_id']}", label_visibility="collapsed")

            locs = page["locators"]
            if filter_valid == "Валидные":
                locs = [l for l in locs if l.get("is_valid")]
            elif filter_valid == "Невалидные":
                locs = [l for l in locs if not l.get("is_valid")]
            if search:
                sl = search.lower()
                locs = [l for l in locs if sl in (l.get("xpath") or "").lower() or sl in (l.get("description") or "").lower()]

            st.caption(f"Показано: {len(locs)} из {len(page['locators'])}")

            if locs:
                loc_df = pd.DataFrame(locs)
                if "validation" in loc_df.columns:
                    loc_df["count"] = loc_df["validation"].apply(
                        lambda v: v.get("count", 0) if isinstance(v, dict) else 0
                    )
                display_cols = ["xpath", "description", "stage", "version", "is_valid", "count"]
                if "selenide_element" in loc_df.columns:
                    display_cols.append("selenide_element")
                existing_cols = [c for c in display_cols if c in loc_df.columns]
                st.dataframe(loc_df[existing_cols], width="stretch", height=300)

                import json
                exp_col1, exp_col2 = st.columns(2)
                with exp_col1:
                    st.download_button(
                        "⬇ JSON",
                        data=json.dumps(locs, ensure_ascii=False, indent=2, default=str),
                        file_name=f"locators_{page['page_id']}.json",
                        mime="application/json",
                        width="stretch",
                        key=f"exp_j_{page['page_id']}",
                    )
                with exp_col2:
                    lines = []
                    for l in locs:
                        if l.get("description"):
                            lines.append(f"# {l['description']}")
                        lines.append(l.get("xpath", ""))
                    st.download_button(
                        "⬇ TXT",
                        data="\n".join(lines),
                        file_name=f"locators_{page['page_id']}.txt",
                        mime="text/plain",
                        width="stretch",
                        key=f"exp_t_{page['page_id']}",
                    )


def _load_pages_with_locators(project_id=None):
    try:
        from src.database.locator_query_service import LocatorQueryService

        async def _fetch():
            svc = LocatorQueryService()
            pages = await svc.get_pages_with_locator(project_id=project_id)
            await svc.close()
            return pages

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(lambda: run_async(_fetch())).result(timeout=15)
    except Exception as e:
        st.warning(f"Не удалось загрузить данные: {e}")
        return []
