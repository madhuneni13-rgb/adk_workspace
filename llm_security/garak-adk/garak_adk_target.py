"""Garak function-generator bridge to api_pentest_agent via the Google ADK API server.

Mirrors llm_security/promptfoo-adk/providers/adk_provider.py: create a fresh
session per prompt, POST /run, extract the last model-authored text event.
A fresh session per call means garak probes never see each other's history -
matching how a real end user would interact with the agent.

Requires the ADK API server running separately:
    adk api_server --host 127.0.0.1 --port 8000

Usage (from the dedicated garak venv, run from this directory so the module
is importable):
    python -m garak --target_type function --target_name garak_adk_target#call_agent \
        --probes promptinject.HijackHateHumansMini --generations 1

Env vars (all optional):
    ADK_BASE_URL        default http://127.0.0.1:8000
    ADK_APP_NAME         default api_pentest_agent
    ADK_TIMEOUT_SECONDS  default 300
"""

from __future__ import annotations

import os
import uuid
from typing import Any, List, Optional

import requests

BASE_URL = os.environ.get("ADK_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
APP_NAME = os.environ.get("ADK_APP_NAME", "api_pentest_agent")
TIMEOUT_SECONDS = int(os.environ.get("ADK_TIMEOUT_SECONDS", "300"))


def _new_identity(prefix: str) -> tuple[str, str]:
    nonce = uuid.uuid4().hex
    return f"garak_{prefix}_{nonce[:10]}", f"{prefix}_{nonce}"


def _extract_final_response(events: Any) -> str:
    """Return text from the last model event in an ADK `/run` response."""
    if not isinstance(events, list):
        return ""
    for event in reversed(events):
        if not isinstance(event, dict):
            continue
        content = event.get("content")
        if not isinstance(content, dict) or content.get("role") != "model":
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        text_parts = [
            str(part["text"])
            for part in parts
            if isinstance(part, dict) and part.get("text")
        ]
        if text_parts:
            return "\n".join(text_parts)
    return ""


def _run_once(prompt: str) -> Optional[str]:
    user_id, session_id = _new_identity("target")
    session_url = f"{BASE_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}"

    try:
        with requests.Session() as client:
            resp = client.post(
                session_url,
                headers={"Content-Type": "application/json"},
                json={},
                timeout=TIMEOUT_SECONDS,
            )
            if not resp.ok:
                return None

            resp = client.post(
                f"{BASE_URL}/run",
                headers={"Content-Type": "application/json"},
                json={
                    "appName": APP_NAME,
                    "userId": user_id,
                    "sessionId": session_id,
                    "newMessage": {"role": "user", "parts": [{"text": prompt}]},
                },
                timeout=TIMEOUT_SECONDS,
            )
            if not resp.ok:
                return None
            try:
                events = resp.json()
            except requests.exceptions.JSONDecodeError:
                return None
    except requests.exceptions.RequestException:
        return None

    output = _extract_final_response(events)
    return output or None


def call_agent(prompt: str, **kwargs) -> List[Optional[str]]:
    """Single-generation entry point for garak.generators.function.Single."""
    return [_run_once(prompt)]


def call_agent_multi(prompt: str, generations: int = 1, **kwargs) -> List[Optional[str]]:
    """Multi-generation entry point for garak.generators.function.Multiple.

    Each generation gets its own fresh ADK session (no shared history).
    """
    return [_run_once(prompt) for _ in range(generations)]
