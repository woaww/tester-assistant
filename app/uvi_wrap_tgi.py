from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import httpx, json, asyncio

app = FastAPI()
TGI_URL = "http://d-gpgpu-a100-01.ct.ahml1.ru:8335/v1/chat/completions"  # твой TGI

@app.post("/v1/chat/completions")
async def openai_compatible_chat(request: Request):
    body = await request.json()

    # 1️⃣ Если есть response_format → вставляем JSON Schema в system‑prompt
    rf = body.get("response_format")
    if rf and isinstance(body.get("messages", []), list):
        schema_text = ""
        if "json_schema" in rf:
            schema_text = (
                "\nYou must respond ONLY as valid JSON matching this schema:\n"
                + json.dumps(rf["json_schema"], indent=2)
            )
        for msg in body["messages"]:
            if msg["role"] == "system":
                msg["content"] += schema_text
                break
        else:
            body["messages"].insert(0, {
                "role": "system",
                "content": "Follow the JSON schema below strictly." + schema_text
            })
        # убираем из тела response_format, чтобы не ломало TGI
        body.pop("response_format", None)

    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(TGI_URL, json=body)
        resp_data = r.json()

    # аккуратно возвращаем как OpenAI совместимый пакет
    if "choices" in resp_data:
        return JSONResponse(resp_data)
    text = resp_data.get("generated_text", "")
    return JSONResponse({
        "id": "chatcmpl-proxy",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}}],
        "model": body.get("model", ""),
    })