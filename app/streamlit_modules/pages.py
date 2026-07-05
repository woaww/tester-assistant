import json
import base64
from datetime import datetime
import os

import pandas as pd
import streamlit as st

from streamlit_modules.ui import section_label
from src.domain_models import (
    AuthConfig,
    ElementSnapshot,
    LlmConfig,
    LocatorResult,
    LocatorRunArtifacts,
    LocatorRunMeta,
    LocatorValidation,
    RunMode,
    RunMetrics,
    RunTimings,
)
from src.el_attr_workflow import AVAILABLE_SELECTORS, DEFAULT_SELECTORS, run_el_attr_workflow
from src.llm_provider import get_browser_llm_model, get_llm_base_url, get_llm_chat_model, get_llm_tools_model
from src.storage.file_store import FileRunStore, make_run_id
from src.secure_store import Credentials, clear_credentials, is_keyring_available, load_credentials, save_credentials
from src.mlflow_utilits import log_locator_run


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name, "") or "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "y", "on")


def _render_locator_panel(locators):
    rows = []
    if locators:
        first = locators[0]
        if isinstance(first, dict):
            for item in locators:
                exists = item.get("exists")
                count = item.get("count")
                status = "❌" if not exists else ("⚠️" if isinstance(count, int) and count > 1 else "✅")
                rows.append({
                    "XPath": item.get("xpath", ""),
                    "Описание": item.get("description") or "—",
                    "Статус": status,
                    "Кол-во": count if count is not None else "?",
                    "SelenideElement": item.get("selenide_element") or "—",
                })
        else:
            rows = [{"XPath": x, "Описание": "—", "Статус": "?", "Кол-во": "?", "SelenideElement": "—"} for x in locators]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего", len(rows))
    c2.metric("✅ Валидных", sum(1 for r in rows if r["Статус"] == "✅"))
    c3.metric("⚠️ Дублей", sum(1 for r in rows if r["Статус"] == "⚠️"))
    c4.metric("❌ Невалидных", sum(1 for r in rows if r["Статус"] == "❌"))

    dl1, dl2, dl3 = st.columns([1, 1, 2])
    with dl1:
        st.download_button("⬇ TXT", data="\n".join(r["XPath"] for r in rows), file_name="locators.txt", mime="text/plain", width="stretch")
    with dl2:
        if st.session_state.get("el_attr_locators_json"):
            st.download_button("⬇ JSON", data=st.session_state["el_attr_locators_json"],
                               file_name=f"locators_{st.session_state.get('el_attr_run_id','run')}.json",
                               mime="application/json", width="stretch")
    with dl3:
        if st.session_state.get("el_attr_run_id"):
            st.caption(f"run: {st.session_state['el_attr_run_id']}")

    view = st.radio(
        "Вид результата",
        options=("Таблица", "Текст"),
        horizontal=True,
        key="locator_view_mode",
        label_visibility="collapsed",
    )
    if view == "Текст":
        lines = []
        for r in rows:
            if r["Описание"] != "—":
                lines.append(f"# {r['Описание']}")
            lines.append(r["XPath"])
            if r["SelenideElement"] != "—":
                lines.append(r["SelenideElement"])
        st.code("\n".join(lines) or "—", language="text")
    else:
        df = pd.DataFrame(rows or [{"XPath": "—", "Описание": "—", "Статус": "—", "Кол-во": "—", "SelenideElement": "—"}])
        df.index = df.index + 1
        df.index.name = "№"
        st.dataframe(df, width="stretch")


def _execute_workflow(**kwargs):
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(progress: float, message: str):
        progress_bar.progress(progress)
        status_text.text(message)

    try:
        # сохранение creds — только если явно включено и keyring доступен
        if kwargs.get("needs_auth") and is_keyring_available() and st.session_state.get("el_attr_save_creds"):
            u = kwargs.get("auth_username")
            p = kwargs.get("auth_password")
            url = kwargs.get("url")
            if u and p and url:
                save_credentials(str(url), Credentials(username=str(u), password=str(p)))

        # project_id / project_name нужны только для сохранения в БД после запуска, не для самого workflow
        wf_kw = {k: v for k, v in kwargs.items() if k not in ("project_id", "project_name")}
        result = run_el_attr_workflow(progress_callback=update_progress, **wf_kw)
        locators = result.get("locators") if isinstance(result, dict) else (result or [])
        selector_stats = result.get("selector_stats") if isinstance(result, dict) else {}
        elements_data = result.get("elements_data") if isinstance(result, dict) else None
        timings = result.get("timings") if isinstance(result, dict) else None
        validation_stats = result.get("validation_stats") if isinstance(result, dict) else None
        runtime_artifacts = result.get("artifacts") if isinstance(result, dict) else None
        total_locators = len(locators)
        valid_locators = sum(1 for item in (locators or []) if isinstance(item, dict) and item.get("exists"))

        run_id = make_run_id()
        mode_model = RunMode(
            kind=("by_tags" if kwargs.get("selectors") else ("by_parent" if kwargs.get("parent_xpath") else "by_description")),
            selectors=kwargs.get("selectors"),
            prompt_description=kwargs.get("prompt_description"),
            parent_xpath=kwargs.get("parent_xpath"),
        )
        auth_model = AuthConfig(
            enabled=bool(kwargs.get("needs_auth")),
            custom_instructions=kwargs.get("auth_custom_instructions"),
        )
        llm_model = LlmConfig(
            base_url=get_llm_base_url(),
            chat_model=get_llm_chat_model(),
            tools_model=get_llm_tools_model(),
            browser_model=get_browser_llm_model(),
            temperature=st.session_state.model_params.get("temperature") if "model_params" in st.session_state else None,
            max_new_tokens=st.session_state.model_params.get("max_new_tokens") if "model_params" in st.session_state else None,
            repetition_penalty=st.session_state.model_params.get("repetition_penalty") if "model_params" in st.session_state else None,
            frequency_penalty=st.session_state.model_params.get("frequency_penalty") if "model_params" in st.session_state else None,
        )
        meta = LocatorRunMeta(
            run_id=run_id,
            url=str(kwargs.get("url") or ""),
            created_at=datetime.utcnow(),
            mode=mode_model,
            auth=auth_model,
            llm=llm_model,
            limits=result.get("limits") if isinstance(result, dict) else {},
        )
        if isinstance(timings, dict):
            meta.timings = RunTimings(
                browser_start_s=timings.get("browser_start_s"),
                auth_s=timings.get("auth_s"),
                collect_elements_s=timings.get("collect_elements_s"),
                generate_locators_s=timings.get("generate_locators_s"),
                validate_locators_s=(validation_stats or {}).get("validate_locators_s") if isinstance(validation_stats, dict) else None,
                fix_locators_s=(validation_stats or {}).get("fix_locators_s") if isinstance(validation_stats, dict) else None,
                total_s=timings.get("total_s"),
            )
        if isinstance(validation_stats, dict):
            meta.metrics = RunMetrics(
                total_elements=sum(len(v) for v in elements_data.values()) if isinstance(elements_data, dict) else 0,
                total_locators=validation_stats.get("total_after_generation") or total_locators,
                valid_after_generation=validation_stats.get("valid_after_generation") or 0,
                invalid_after_generation=validation_stats.get("invalid_after_generation") or 0,
                fixed_valid=validation_stats.get("fixed_valid") or 0,
                still_invalid=validation_stats.get("still_invalid") or 0,
                accuracy=validation_stats.get("accuracy"),
                fix_rate=validation_stats.get("fix_rate"),
                correctness=validation_stats.get("correctness"),
            )

        flat_elements: list[dict] = []
        if isinstance(elements_data, dict):
            for group, elements in elements_data.items():
                if not isinstance(elements, list):
                    continue
                for el in elements:
                    if isinstance(el, dict):
                        el_copy = dict(el)
                        el_copy["_selector_group"] = group
                        flat_elements.append(el_copy)

        elements_models: list[ElementSnapshot] = []
        for idx, el in enumerate(flat_elements):
            elements_models.append(
                ElementSnapshot(
                    element_id=f"e{idx}",
                    tag=el.get("tag"),
                    attributes=el.get("attributes") or {},
                    textContent=el.get("textContent"),
                    parent=el.get("parent"),
                    siblings=el.get("siblings"),
                    selector_group=el.get("_selector_group"),
                )
            )

        locator_models: list[LocatorResult] = []
        for item in locators or []:
            if not isinstance(item, dict) or not item.get("xpath"):
                continue
            original_index = item.get("original_index")
            element_id = f"e{original_index}" if isinstance(original_index, int) else "e?"
            locator_models.append(
                LocatorResult(
                    element_id=element_id,
                    xpath=item.get("xpath", ""),
                    description=item.get("description", "") or "",
                    selenide_element=item.get("selenide_element"),
                    original_index=original_index if isinstance(original_index, int) else None,
                    validation=LocatorValidation(exists=bool(item.get("exists")), count=int(item.get("count") or 0)),
                    stage=str(item.get("stage") or "generated"),
                )
            )

        artifacts = LocatorRunArtifacts(meta=meta, elements=elements_models, locators=locator_models)
        store = FileRunStore()
        store.save_run(artifacts, include_elements=True)
        # сохраняем сырые ответы LLM, если они присутствуют в локаторах
        raw_seen = 0
        for i, item in enumerate(locators or []):
            if not isinstance(item, dict):
                continue
            raw = item.get("_raw_llm_meta")
            if raw and raw_seen < 50:
                store.save_raw_llm(run_id, f"chunk_{i:04d}.json", raw)
                raw_seen += 1

        # сохраняем журнал процесса и скриншоты страницы в runs/<run_id>/
        if isinstance(runtime_artifacts, dict):
            events = runtime_artifacts.get("events") or []
            if isinstance(events, list) and events:
                store.save_event_log(run_id, events)

            screenshots = runtime_artifacts.get("screenshots") or []
            if isinstance(screenshots, list):
                for shot in screenshots:
                    if not isinstance(shot, dict):
                        continue
                    content_b64 = shot.get("content_b64")
                    if not content_b64:
                        continue
                    try:
                        raw = base64.b64decode(content_b64)
                        store.save_screenshot_bytes(
                            run_id,
                            str(shot.get("name") or f"shot_{len(screenshots)}"),
                            raw,
                        )
                    except Exception:
                        continue
        st.session_state["el_attr_run_id"] = run_id
        st.session_state["el_attr_locators_json"] = json.dumps(
            [x.model_dump(mode="json") for x in artifacts.locators], ensure_ascii=False, indent=2
        )

        # Опционально: записываем результаты в Postgres для “управления данными”
        if _env_bool("DB_ENABLED", False):
            try:
                from src.database.locator_db_service import LocatorDbService

                LocatorDbService().save_run(
                    url=meta.url,
                    run_mode=meta.mode.kind,
                    locators=[x.model_dump(mode="json") for x in artifacts.locators],
                    elements_data=[x.model_dump(mode="json") for x in artifacts.elements],
                    llm_config=meta.llm.model_dump(mode="json") if meta.llm else None,
                    auth_config=meta.auth.model_dump(mode="json") if meta.auth else None,
                    metrics=meta.metrics.model_dump(mode="json") if meta.metrics else None,
                    timings=meta.timings.model_dump(mode="json") if meta.timings else None,
                    artifacts_path=str(store.get_run_dir(run_id)),
                    project_id=kwargs.get("project_id"),
                    project_name=kwargs.get("project_name"),
                )
            except Exception as e:
                st.warning(f"Не удалось сохранить результаты в БД: {e}")

        st.success("Готово.")
        st.caption(f"Локаторов: **{total_locators}**, валидных: **{valid_locators}**.")
        if isinstance(meta.metrics, RunMetrics):
            cols = st.columns(3)
            cols[0].metric("Accuracy", f"{(meta.metrics.accuracy or 0)*100:.1f}%" if meta.metrics.accuracy is not None else "—")
            cols[1].metric("Fix rate", f"{(meta.metrics.fix_rate or 0)*100:.1f}%" if meta.metrics.fix_rate is not None else "—")
            cols[2].metric("Correctness", f"{(meta.metrics.correctness or 0)*100:.1f}%" if meta.metrics.correctness is not None else "—")
        # MLflow: логируем параметры и метрики запуска (если включено в env)
        log_locator_run(
            run_id=run_id,
            params={
                "url": meta.url,
                "mode": meta.mode.kind,
                "chunk_size": (meta.limits or {}).get("chunk_size"),
                "fix_chunk_size": (meta.limits or {}).get("fix_chunk_size"),
                "max_total_elements": (meta.limits or {}).get("max_total_elements"),
                "max_children_elements": (meta.limits or {}).get("max_children_elements"),
                "llm_chat_model": meta.llm.chat_model if meta.llm else None,
                "llm_tools_model": meta.llm.tools_model if meta.llm else None,
                "llm_browser_model": meta.llm.browser_model if meta.llm else None,
            },
            metrics={
                "total_locators": float(total_locators),
                "valid_locators": float(valid_locators),
                "accuracy": float(meta.metrics.accuracy) if isinstance(meta.metrics, RunMetrics) and meta.metrics.accuracy is not None else None,
                "fix_rate": float(meta.metrics.fix_rate) if isinstance(meta.metrics, RunMetrics) and meta.metrics.fix_rate is not None else None,
                "correctness": float(meta.metrics.correctness) if isinstance(meta.metrics, RunMetrics) and meta.metrics.correctness is not None else None,
                "total_s": float(meta.timings.total_s) if isinstance(meta.timings, RunTimings) and meta.timings.total_s is not None else None,
                "generate_locators_s": float(meta.timings.generate_locators_s) if isinstance(meta.timings, RunTimings) and meta.timings.generate_locators_s is not None else None,
                "validate_locators_s": float(meta.timings.validate_locators_s) if isinstance(meta.timings, RunTimings) and meta.timings.validate_locators_s is not None else None,
                "fix_locators_s": float(meta.timings.fix_locators_s) if isinstance(meta.timings, RunTimings) and meta.timings.fix_locators_s is not None else None,
            },
            tags={
                "component": "locator-generator",
                "db_enabled": _env_bool("DB_ENABLED", False),
            },
        )
        st.session_state["el_attr_locators"] = locators or []
        st.session_state["el_attr_selector_stats"] = selector_stats or {}
        return total_locators
    except Exception as e:
        st.error(f"Ошибка при выполнении сценария: {e}")
        return None
    finally:
        progress_bar.empty()
        status_text.empty()


def main_page():
    # Одна колонка на всю ширину контейнера (с layout="centered" так удобнее, чем два узких столбца).
    section_label("Параметры запуска")

    target_url = st.text_input("URL страницы", placeholder="https://example.com")
    mode = st.radio(
        "Режим",
        options=("По тегам", "По описанию", "От родителя"),
        horizontal=True,
        key="el_attr_mode",
    )

    selected_selectors, prompt_description, parent_xpath = [], "", ""
    if mode == "По тегам":
        selected_selectors = st.multiselect(
            "Теги",
            options=AVAILABLE_SELECTORS,
            default=DEFAULT_SELECTORS,
            key="el_attr_selectors",
        )
    elif mode == "По описанию":
        prompt_description = st.text_input("Описание элемента", key="el_attr_prompt_desc")
    else:
        parent_xpath = st.text_input("XPath родителя", key="el_attr_parent_xpath")

    selected_project_id, selected_project_name = None, None
    if _env_bool("DB_ENABLED", False):
        from streamlit_modules.projects_page import get_project_list_for_selector, get_project_id_from_selection

        project_options = get_project_list_for_selector()
        if project_options:
            labels = [opt.split("|", 1)[1] for opt in project_options]
            sel = st.selectbox("Проект", options=labels, index=0, key="generator_project")
            selected_project_id = get_project_id_from_selection(project_options[labels.index(sel)])
            selected_project_name = sel

    needs_auth = st.checkbox("Требуется авторизация", value=False, key="el_attr_needs_auth")
    keyring_enabled = False
    auth_username, auth_password = "", ""
    auth_custom_instructions = ""

    if needs_auth:
        keyring_enabled = is_keyring_available()
        c1, c2 = st.columns(2)
        auth_username = c1.text_input("Логин", key="el_attr_auth_username")
        auth_password = c2.text_input("Пароль", type="password", key="el_attr_auth_password")
        if keyring_enabled:
            stored = load_credentials(target_url)
            if stored and not auth_username and not auth_password:
                auth_username, auth_password = stored.username, stored.password
                st.caption("Используются сохранённые учётные данные.")
        auth_custom_instructions = st.text_area(
            "Шаги авторизации для агента",
            key="el_attr_auth_custom_instructions",
            help="Кратко опишите, куда нажать и что ввести (логин/пароль подставятся из полей выше).",
        )
        with st.expander("Хранение учётных данных"):
            if not keyring_enabled:
                st.info("`keyring` недоступен.")
            else:
                st.checkbox("Запомнить логин/пароль", value=False, key="el_attr_save_creds")
                if st.button("Удалить сохранённые данные"):
                    clear_credentials(target_url)
                    st.success("Удалено.")

    generate_selenide = st.checkbox("Генерировать SelenideElement", value=False, key="el_attr_generate_selenide")
    run_btn = st.button("Запустить", type="primary", width="stretch")

    st.divider()
    section_label("Результат")

    auth_kwargs = {
        "needs_auth": needs_auth,
        "auth_username": auth_username if needs_auth else None,
        "auth_password": auth_password if needs_auth else None,
        "auth_custom_instructions": auth_custom_instructions if needs_auth else None,
    }
    limit_kwargs = {
        "chunk_size": int(st.session_state.get("el_attr_chunk_size", 6)),
        "fix_chunk_size": int(st.session_state.get("el_attr_fix_chunk_size", 5)),
        "max_total_elements": int(st.session_state.get("el_attr_max_total_elements", 400)),
        "max_children_elements": int(st.session_state.get("el_attr_max_children_elements", 400)),
    }
    project_kwargs = {"project_id": selected_project_id, "project_name": selected_project_name}

    if run_btn:
        if not target_url or not target_url.strip():
            st.warning("Введите URL страницы.")
        elif needs_auth and (not auth_username or not auth_password):
            st.warning("Укажите логин и пароль.")
        elif mode == "По описанию" and not prompt_description:
            st.warning("Введите описание элемента.")
        elif mode == "От родителя" and not parent_xpath:
            st.warning("Введите XPath родителя.")
        else:
            kw = dict(
                url=target_url,
                generate_selenide=generate_selenide,
                **auth_kwargs,
                **limit_kwargs,
                **project_kwargs,
            )
            if mode == "По тегам":
                kw["selectors"] = selected_selectors or DEFAULT_SELECTORS
            elif mode == "По описанию":
                kw.update(selectors=None, prompt_description=prompt_description)
            else:
                kw.update(selectors=None, prompt_description=None, parent_xpath=parent_xpath)
            total = _execute_workflow(**kw)
            if total == 0:
                st.warning("Локаторы не найдены.")

    saved_locators = st.session_state.get("el_attr_locators")
    selector_stats = st.session_state.get("el_attr_selector_stats", {})

    if not saved_locators and not run_btn:
        st.info("Введите URL и нажмите «Запустить».")

    if selector_stats:
        cols = st.columns(min(len(selector_stats), 4))
        for col, (sel, count) in zip(cols, selector_stats.items()):
            col.metric(f"`{sel}`", count)

    if saved_locators:
        _render_locator_panel(saved_locators)
    elif saved_locators == []:
        st.warning("Локаторы не сгенерированы.")


