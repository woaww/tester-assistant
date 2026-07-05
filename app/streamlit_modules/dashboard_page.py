"""Страница Dashboard с аналитикой и метриками качества локаторов."""

import concurrent.futures

import pandas as pd
import streamlit as st

from streamlit_modules.async_bridge import run_async


def dashboard_page():
    from streamlit_modules.projects_page import get_project_list_for_selector, get_project_id_from_selection

    project_options = get_project_list_for_selector()
    selected_project_id = None
    if project_options:
        project_labels = ["Все проекты"] + [opt.split("|", 1)[1] for opt in project_options]
        selected_label = st.selectbox(
            "Проект", options=project_labels, index=0, key="dashboard_project_filter"
        )
        if selected_label != "Все проекты":
            idx = project_labels.index(selected_label)
            selected_project_id = get_project_id_from_selection(project_options[idx - 1])

    stats = _load_stats(project_id=selected_project_id)
    if not stats:
        st.info("Данных пока нет. Сгенерируйте локаторы на странице Генератор.")
        return

    if stats.get("invalid_locators") is not None:
        invalid_n = int(stats["invalid_locators"])
    else:
        invalid_n = max(0, int(stats["locators_count"]) - int(stats["valid_locators"]))
    corr = stats.get("avg_correctness")
    corr_label = f"{corr * 100:.1f}%" if corr is not None else "—"

    st.subheader("Обзор")
    r1a, r1b, r1c, r1d = st.columns(4)
    r1a.metric("Проекты", stats["projects_count"])
    r1b.metric("Страницы", stats["pages_count"])
    r1c.metric("Запуски", stats["runs_count"])
    r1d.metric("Локаторы", stats["locators_count"])

    r2a, r2b, r2c, r2d = st.columns(4)
    r2a.metric("Валидные", stats["valid_locators"])
    r2b.metric("Исправленные", stats["fixed_locators"])
    r2c.metric("Невалидные", invalid_n)
    r2d.metric("Средняя корректность", corr_label)

    st.subheader("Последние запуски")
    recent_runs = _load_recent_runs(limit=10, project_id=selected_project_id)
    if recent_runs:
        recent_df = pd.DataFrame(recent_runs)
        recent_df["created_at"] = pd.to_datetime(recent_df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
        recent_df["correctness"] = recent_df.apply(
            lambda r: round(
                (r["valid_locators"] + r["fixed_locators"]) / max(r["total_elements"], 1) * 100, 1
            ),
            axis=1,
        )
        display_cols = ["run_id", "project_name", "url", "run_mode", "total_elements",
                        "valid_locators", "invalid_locators", "fixed_locators", "correctness", "created_at"]
        st.dataframe(recent_df[display_cols], width="stretch", hide_index=True)
    else:
        st.info("Нет данных о запусках")

    st.subheader("Стабильность XPath")
    stability = _load_stability_report()
    if stability:
        st.dataframe(pd.DataFrame(stability), width="stretch", hide_index=True)
    else:
        st.caption("Пока нет данных для отчёта.")

    st.subheader("Активность по проектам")
    project_stats = _load_project_stats()
    if project_stats:
        proj_df = pd.DataFrame(project_stats)
        proj_df["last_run_at"] = pd.to_datetime(proj_df["last_run_at"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(proj_df, width="stretch", hide_index=True)
    else:
        st.info("Нет данных по проектам")


def _load_stats(project_id=None):
    try:
        from src.database.locator_query_service import LocatorQueryService

        async def _fetch():
            svc = LocatorQueryService()
            if project_id:
                runs = await svc.get_runs_history(limit=1000, project_id=project_id)
                total_valid = sum(r.get("valid_locators", 0) for r in runs)
                total_fixed = sum(r.get("fixed_locators", 0) for r in runs)
                total_invalid = sum((r.get("invalid_locators") or 0) for r in runs)
                accuracies = [m["correctness"] for r in runs if isinstance((m := r.get("metrics") or {}), dict) and m.get("correctness") is not None]
                avg_c = sum(accuracies) / len(accuracies) if accuracies else None
                await svc.close()
                return {
                    "projects_count": 1,
                    "pages_count": len(set(r.get("url") for r in runs)),
                    "runs_count": len(runs),
                    "locators_count": sum(r.get("total_elements", 0) for r in runs),
                    "valid_locators": total_valid,
                    "fixed_locators": total_fixed,
                    "invalid_locators": total_invalid,
                    "history_entries": 0,
                    "avg_correctness": round(avg_c, 3) if avg_c else None,
                }
            else:
                stats = await svc.get_dashboard_stats()
                await svc.close()
                return stats

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(lambda: run_async(_fetch())).result(timeout=15)
    except Exception as e:
        st.warning(f"Не удалось загрузить статистику: {e}")
        return None


def _load_project_stats():
    try:
        from src.database.locator_query_service import LocatorQueryService

        async def _fetch():
            svc = LocatorQueryService()
            stats = await svc.get_runs_by_project()
            await svc.close()
            return stats

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(lambda: run_async(_fetch())).result(timeout=15)
    except Exception:
        return []


def _load_recent_runs(limit=10, project_id=None):
    try:
        from src.database.locator_query_service import LocatorQueryService

        async def _fetch():
            svc = LocatorQueryService()
            runs = await svc.get_runs_history(limit=limit, project_id=project_id)
            await svc.close()
            return runs

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(lambda: run_async(_fetch())).result(timeout=15)
    except Exception as e:
        st.warning(f"Не удалось загрузить запуски: {e}")
        return []


def _load_stability_report():
    try:
        from src.database.locator_query_service import LocatorQueryService

        async def _fetch():
            svc = LocatorQueryService()
            report = await svc.get_stability_report(limit=30)
            await svc.close()
            return report

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(lambda: run_async(_fetch())).result(timeout=15)
    except Exception:
        return []
