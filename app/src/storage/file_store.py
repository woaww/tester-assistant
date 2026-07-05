from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from src.domain_models import LocatorRunArtifacts


def _default_runs_dir() -> Path:
    # По умолчанию сохраняем в корень репозитория: <repo>/runs
    # file_store.py находится в app/src/storage/, значит repo = parents[3]
    repo_root = Path(__file__).resolve().parents[3]
    env_dir = os.getenv("RUNS_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return (repo_root / "runs").resolve()


def _json_dump(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _model_dump(obj: BaseModel | dict | list) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    return obj


def make_run_id(now: datetime | None = None) -> str:
    ts = (now or datetime.utcnow()).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{uuid4().hex[:8]}"


@dataclass(frozen=True)
class RunPaths:
    run_id: str
    run_dir: Path
    meta_json: Path
    locators_json: Path
    locators_txt: Path
    elements_json: Path


class FileRunStore:
    def __init__(self, runs_dir: Path | None = None):
        self.runs_dir = runs_dir or _default_runs_dir()
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, run_id: str | None = None) -> RunPaths:
        rid = run_id or make_run_id()
        run_dir = self.runs_dir / rid
        run_dir.mkdir(parents=True, exist_ok=False)
        return RunPaths(
            run_id=rid,
            run_dir=run_dir,
            meta_json=run_dir / "meta.json",
            locators_json=run_dir / "locators.json",
            locators_txt=run_dir / "locators.txt",
            elements_json=run_dir / "elements.json",
        )

    def save_run(self, artifacts: LocatorRunArtifacts, include_elements: bool = True) -> RunPaths:
        paths = self.create_run(artifacts.meta.run_id)

        _json_dump(paths.meta_json, _model_dump(artifacts.meta))

        locators_payload = [_model_dump(x) for x in artifacts.locators]
        _json_dump(paths.locators_json, locators_payload)

        locators_lines: list[str] = []
        for item in artifacts.locators:
            line = item.xpath
            if item.description:
                line = f"{line}  # {item.description}"
            locators_lines.append(line)
            if item.selenide_element:
                locators_lines.append(item.selenide_element)
        paths.locators_txt.write_text("\n".join(locators_lines) + ("\n" if locators_lines else ""), encoding="utf-8")

        if include_elements:
            elements_payload = [_model_dump(x) for x in artifacts.elements]
            _json_dump(paths.elements_json, elements_payload)

        return paths

    def save_raw_llm(self, run_id: str, name: str, payload: Any) -> Path:
        """
        Сохраняет сырые ответы LLM для воспроизводимости.
        """
        run_dir = self.runs_dir / run_id
        raw_dir = run_dir / "raw_llm"
        raw_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in name)
        path = raw_dir / safe
        if path.suffix.lower() not in {".json", ".txt"}:
            path = path.with_suffix(".json")
        if path.suffix.lower() == ".txt":
            path.write_text(str(payload), encoding="utf-8")
        else:
            _json_dump(path, payload)
        return path

    def get_run_dir(self, run_id: str) -> Path:
        return (self.runs_dir / run_id).resolve()

    def save_event_log(self, run_id: str, events: list[dict]) -> Path:
        run_dir = self.runs_dir / run_id
        logs_dir = run_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        path = logs_dir / "workflow_events.jsonl"
        lines = [json.dumps(event, ensure_ascii=False, default=str) for event in events]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return path

    def save_screenshot_bytes(self, run_id: str, name: str, content: bytes) -> Path:
        run_dir = self.runs_dir / run_id
        shot_dir = run_dir / "screenshots"
        shot_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in name)
        path = shot_dir / (safe if safe.lower().endswith(".png") else f"{safe}.png")
        path.write_bytes(content)
        return path

