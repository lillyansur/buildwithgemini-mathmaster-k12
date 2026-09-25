"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.
"""

import json
import os
import re
import uuid

import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest
from a2a.utils.constants import (
    PROTOCOL_VERSION_1_0,
    VERSION_HEADER,
    TransportProtocol,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from google.protobuf.json_format import MessageToDict

RESOURCE = os.environ.get(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/815349329427/locations/us-east1/reasoningEngines/7116872684780126208",
)
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)

_A2UI_MIME = "application/json+a2ui"
_A2UI_TAG_REGEX = re.compile(r"<a2ui-json>(.*?)</a2ui-json>", re.DOTALL)

# Application Default Credentials refreshed per request
_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
        VERSION_HEADER: PROTOCOL_VERSION_1_0,
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


# Context ID tracking per user
_contexts: dict[str, str] = {}


def _extract_parts(part_dicts: list[dict]) -> list[dict]:
    """Extract text and A2UI data parts."""
    out: list[dict] = []
    for p in part_dicts:
        text = p.get("text")
        if text:
            match = _A2UI_TAG_REGEX.search(text)
            if match:
                clean_text = _A2UI_TAG_REGEX.sub("", text).strip()
                if clean_text:
                    out.append({"kind": "text", "text": clean_text})
                try:
                    a2ui_data = json.loads(match.group(1).strip())
                    if isinstance(a2ui_data, list):
                        for item in a2ui_data:
                            out.append({"kind": "a2ui", "data": item})
                    elif isinstance(a2ui_data, dict):
                        out.append({"kind": "a2ui", "data": a2ui_data})
                except Exception:
                    pass
            else:
                out.append({"kind": "text", "text": text})

        data = p.get("data")
        if data is not None:
            mime = p.get("metadata", {}).get("mimeType") or p.get("mediaType")
            if mime == _A2UI_MIME or isinstance(data, (dict, list)):
                if isinstance(data, list):
                    for item in data:
                        out.append({"kind": "a2ui", "data": item})
                else:
                    out.append({"kind": "a2ui", "data": data})

        url = p.get("url")
        if url:
            out.append({"kind": "text", "text": url})

    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message_text = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        config = ClientConfig(
            httpx_client=client,
            supported_protocol_bindings=[
                TransportProtocol.JSONRPC,
                TransportProtocol.HTTP_JSON,
            ],
        )
        a2a_client = await create_client(A2A_BASE, config)

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=message_text)],
            context_id=_contexts.get(user_id, ""),
        )

        async for chunk in a2a_client.send_message(SendMessageRequest(message=msg)):
            d = MessageToDict(chunk)
            if "statusUpdate" in d and d["statusUpdate"].get("contextId"):
                _contexts[user_id] = d["statusUpdate"]["contextId"]
            if "artifactUpdate" in d:
                if d["artifactUpdate"].get("contextId"):
                    _contexts[user_id] = d["artifactUpdate"]["contextId"]
                artifact = d["artifactUpdate"].get("artifact", {})
                parts.extend(_extract_parts(artifact.get("parts", [])))
            elif "task" in d:
                if d["task"].get("contextId"):
                    _contexts[user_id] = d["task"]["contextId"]
                for artifact in d["task"].get("artifacts", []):
                    parts.extend(_extract_parts(artifact.get("parts", [])))
            elif "message" in d:
                parts.extend(_extract_parts(d["message"].get("parts", [])))

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
