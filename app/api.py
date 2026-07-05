from __future__ import annotations

import sys
from pathlib import Path

# Каталог app/ должен быть в sys.path, чтобы находился пакет src (и при запуске uvicorn из корня репозитория).
_APP_ROOT = Path(__file__).resolve().parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.el_attr_workflow import run_el_attr_workflow


app = FastAPI(title="Locator Generator API", version="0.1.0")


class GenerateRequest(BaseModel):
    url: str
    mode: str = Field(description="by_tags | by_description | by_parent")
    selectors: list[str] | None = None
    prompt_description: str | None = None
    parent_xpath: str | None = None
    generate_selenide: bool = False

    needs_auth: bool = False
    auth_username: str | None = None
    auth_password: str | None = None
    auth_custom_instructions: str | None = None

    chunk_size: int = 10
    fix_chunk_size: int = 10
    max_total_elements: int = 1000
    max_children_elements: int = 1000


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/generate-locators")
def generate_locators(req: GenerateRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="url is required")

    if req.mode == "by_tags":
        selectors = req.selectors
        prompt_description = None
        parent_xpath = None
    elif req.mode == "by_description":
        selectors = None
        prompt_description = req.prompt_description
        parent_xpath = None
        if not prompt_description:
            raise HTTPException(status_code=400, detail="prompt_description is required for by_description")
    elif req.mode == "by_parent":
        selectors = None
        prompt_description = None
        parent_xpath = req.parent_xpath
        if not parent_xpath:
            raise HTTPException(status_code=400, detail="parent_xpath is required for by_parent")
    else:
        raise HTTPException(status_code=400, detail="mode must be one of: by_tags, by_description, by_parent")

    try:
        result = run_el_attr_workflow(
            url=req.url,
            selectors=selectors,
            prompt_description=prompt_description,
            parent_xpath=parent_xpath,
            generate_selenide=req.generate_selenide,
            needs_auth=req.needs_auth,
            auth_username=req.auth_username,
            auth_password=req.auth_password,
            auth_custom_instructions=req.auth_custom_instructions,
            chunk_size=req.chunk_size,
            fix_chunk_size=req.fix_chunk_size,
            max_total_elements=req.max_total_elements,
            max_children_elements=req.max_children_elements,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

