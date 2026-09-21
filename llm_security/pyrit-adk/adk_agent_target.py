"""PyRIT PromptTarget bridge to api_pentest_agent via the Google ADK API server.

Mirrors llm_security/promptfoo-adk/providers/adk_provider.py and
llm_security/garak-adk/garak_adk_target.py: creates a fresh ADK
user/session per send, POSTs /run, and extracts the last model-authored
text event. Declared single-turn (PyRIT's base default) - each attack turn
gets its own isolated ADK session, matching the methodology used by the
other two tools so results are comparable.

Requires the ADK API server running separately:
    adk api_server --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx

from pyrit.models import ComponentIdentifier, Message, construct_response_from_request
from pyrit.prompt_target.common.prompt_target import PromptTarget
from pyrit.prompt_target.common.target_configuration import TargetConfiguration
from pyrit.prompt_target.common.utils import limit_requests_per_minute

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_APP_NAME = "api_pentest_agent"
DEFAULT_TIMEOUT_SECONDS = 300.0


class ADKAgentTarget(PromptTarget):
    """PyRIT prompt target for api_pentest_agent, reached through its ADK API server."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        app_name: str = DEFAULT_APP_NAME,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_requests_per_minute: int | None = None,
        custom_configuration: TargetConfiguration | None = None,
    ) -> None:
        base_url = base_url.rstrip("/")
        super().__init__(
            endpoint=f"{base_url}/run",
            model_name=app_name,
            max_requests_per_minute=max_requests_per_minute,
            custom_configuration=custom_configuration,
        )
        self._base_url = base_url
        self._app_name = app_name
        self._timeout_seconds = timeout_seconds

    def _build_identifier(self) -> ComponentIdentifier:
        return self._create_identifier(params={"app_name": self._app_name})

    @staticmethod
    def _new_identity(prefix: str) -> tuple[str, str]:
        nonce = uuid.uuid4().hex
        return f"pyrit_{prefix}_{nonce[:10]}", f"{prefix}_{nonce}"

    @staticmethod
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

    @limit_requests_per_minute
    async def _send_prompt_to_target_async(self, *, normalized_conversation: list[Message]) -> list[Message]:
        message = normalized_conversation[-1]
        request = message.message_pieces[0]
        prompt_text = request.converted_value

        user_id, session_id = self._new_identity("target")
        session_url = f"{self._base_url}/apps/{self._app_name}/users/{user_id}/sessions/{session_id}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                session_resp = await client.post(
                    session_url,
                    headers={"Content-Type": "application/json"},
                    json={},
                )
                session_resp.raise_for_status()

                run_resp = await client.post(
                    f"{self._base_url}/run",
                    headers={"Content-Type": "application/json"},
                    json={
                        "appName": self._app_name,
                        "userId": user_id,
                        "sessionId": session_id,
                        "newMessage": {"role": "user", "parts": [{"text": prompt_text}]},
                    },
                )
                run_resp.raise_for_status()
                events = run_resp.json()
        except httpx.HTTPError as exc:
            logger.error(f"ADK request failed: {exc}")
            output = f"[ADK request error] {exc}"
        else:
            output = self._extract_final_response(events) or "[ADK returned no final model text]"

        logger.info(f'Received response from api_pentest_agent: "{output[:200]}"')

        response_entry = construct_response_from_request(request=request, response_text_pieces=[output])
        return [response_entry]
