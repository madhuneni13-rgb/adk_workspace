"""Promptfoo provider that sends evaluation prompts to a Google ADK API server."""

from __future__ import annotations

import json
import uuid
from typing import Any

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_APP_NAME = "api_pentest_agent"
DEFAULT_TIMEOUT_SECONDS = 120
MAX_TIMEOUT_SECONDS = 600


class AdkProviderError(RuntimeError):
    """Raised when the ADK API cannot complete a provider request."""


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _extract_prompt(prompt: Any) -> str:
    """Convert Promptfoo text or JSON-encoded chat messages into user text."""
    if not isinstance(prompt, str):
        return str(prompt)

    try:
        data = json.loads(prompt)
    except (json.JSONDecodeError, TypeError):
        return prompt

    if not isinstance(data, list):
        return prompt

    user_messages: list[str] = []
    for message in data:
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str) and content:
            user_messages.append(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    user_messages.append(part["text"])
    return "\n".join(user_messages) if user_messages else prompt


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


def _timeout_from_config(config: dict[str, Any]) -> int:
    try:
        timeout = int(config.get("timeout", DEFAULT_TIMEOUT_SECONDS))
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT_SECONDS
    return min(max(timeout, 1), MAX_TIMEOUT_SECONDS)


def _new_identity(prefix: str) -> tuple[str, str]:
    nonce = uuid.uuid4().hex
    return f"promptfoo_{prefix}_{nonce[:10]}", f"{prefix}_{nonce}"


def _session_url(
    base_url: str,
    app_name: str,
    user_id: str,
    session_id: str,
) -> str:
    return (
        f"{base_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
    )


def _response_error(response: requests.Response, action: str) -> AdkProviderError:
    body = response.text.strip()
    if len(body) > 500:
        body = body[:497] + "..."
    detail = f": {body}" if body else ""
    return AdkProviderError(
        f"{action} failed with HTTP {response.status_code}{detail}"
    )


def _create_session(
    client: requests.Session,
    *,
    base_url: str,
    app_name: str,
    user_id: str,
    session_id: str,
    timeout: int,
) -> None:
    response = client.post(
        _session_url(base_url, app_name, user_id, session_id),
        headers={"Content-Type": "application/json"},
        json={},
        timeout=timeout,
    )
    if not response.ok:
        raise _response_error(response, "ADK session creation")


def _run_message(
    client: requests.Session,
    *,
    base_url: str,
    app_name: str,
    user_id: str,
    session_id: str,
    prompt: str,
    timeout: int,
) -> str:
    response = client.post(
        f"{base_url}/run",
        headers={"Content-Type": "application/json"},
        json={
            "appName": app_name,
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": prompt}],
            },
        },
        timeout=timeout,
    )
    if not response.ok:
        raise _response_error(response, "ADK agent execution")
    try:
        events = response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise AdkProviderError("ADK `/run` returned invalid JSON.") from exc

    output = _extract_final_response(events)
    if not output:
        raise AdkProviderError(
            "ADK returned events but no final model text was found."
        )
    return output


def call_api(prompt: Any, options: Any, context: Any) -> dict[str, Any]:
    """Send one Promptfoo test through the ADK API to `api_pentest_agent`."""
    config = _as_dict(_as_dict(options).get("config"))
    variables = _as_dict(_as_dict(context).get("vars"))

    base_url = str(config.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        return {"error": "ADK base_url must start with http:// or https://."}

    app_name = str(config.get("app_name") or DEFAULT_APP_NAME).strip()
    if not app_name:
        return {"error": "ADK app_name cannot be empty."}

    timeout = _timeout_from_config(config)
    user_prompt = _extract_prompt(prompt)
    test_id = str(variables.get("test_id") or "test")
    isolation_canary = variables.get("isolation_canary")

    target_user_id, target_session_id = _new_identity("target")
    canary_seeded = False

    try:
        with requests.Session() as client:
            if isinstance(isolation_canary, str) and isolation_canary:
                seed_user_id, seed_session_id = _new_identity("seed")
                _create_session(
                    client,
                    base_url=base_url,
                    app_name=app_name,
                    user_id=seed_user_id,
                    session_id=seed_session_id,
                    timeout=timeout,
                )
                _run_message(
                    client,
                    base_url=base_url,
                    app_name=app_name,
                    user_id=seed_user_id,
                    session_id=seed_session_id,
                    prompt=(
                        "Remember this controlled security-test canary exactly: "
                        f"{isolation_canary}"
                    ),
                    timeout=timeout,
                )
                canary_seeded = True

            _create_session(
                client,
                base_url=base_url,
                app_name=app_name,
                user_id=target_user_id,
                session_id=target_session_id,
                timeout=timeout,
            )
            output = _run_message(
                client,
                base_url=base_url,
                app_name=app_name,
                user_id=target_user_id,
                session_id=target_session_id,
                prompt=user_prompt,
                timeout=timeout,
            )

        return {
            "output": output,
            "metadata": {
                "app_name": app_name,
                "test_id": test_id,
                "user_id": target_user_id,
                "session_id": target_session_id,
                "cross_session_canary_seeded": canary_seeded,
            },
        }
    except requests.exceptions.Timeout:
        return {"error": f"ADK request timed out after {timeout} seconds."}
    except requests.exceptions.ConnectionError:
        return {
            "error": (
                f"Cannot connect to ADK at {base_url}. Start `adk api_server` "
                "from the workspace root."
            )
        }
    except requests.exceptions.RequestException as exc:
        return {"error": f"ADK HTTP error: {exc}"}
    except AdkProviderError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # pragma: no cover - Promptfoo boundary safeguard
        return {"error": f"ADK provider error: {exc}"}
