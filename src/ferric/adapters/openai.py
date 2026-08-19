"""Normalise OpenAI chat completion requests and responses."""

from __future__ import annotations

import json
import os
from typing import Any

from ferric.schema import (
    AssistantMessage,
    ErrorEvent,
    ErrorPayload,
    Event,
    MessagePayload,
    ToolCall,
    ToolCallPayload,
    ToolResult,
    ToolResultPayload,
    UserMessage,
)


def _plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(child) for child in value]
    return value


def _arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {"_raw": value}
        return decoded if isinstance(decoded, dict) else {"_value": decoded}
    return {"_value": _plain(value)}


def normalise_openai(
    request: dict[str, Any],
    response: Any | None = None,
    error: BaseException | None = None,
) -> list[Event]:
    """Convert one OpenAI chat completion exchange into typed events."""

    events: list[Event] = []
    for message in _plain(request.get("messages", [])):
        role = message.get("role", "user")
        if role == "assistant":
            content = message.get("content")
            if content is not None:
                events.append(
                    AssistantMessage(
                        index=len(events),
                        payload=MessagePayload(content=content, source_role=role),
                    )
                )
            for call in message.get("tool_calls", []):
                function = call.get("function", {})
                events.append(
                    ToolCall(
                        index=len(events),
                        payload=ToolCallPayload(
                            name=function.get("name", "unknown_tool"),
                            arguments=_arguments(function.get("arguments", {})),
                            call_id=call.get("id"),
                        ),
                    )
                )
        elif role == "tool":
            events.append(
                ToolResult(
                    index=len(events),
                    payload=ToolResultPayload(
                        content=message.get("content"),
                        name=message.get("name"),
                        call_id=message.get("tool_call_id"),
                    ),
                )
            )
        else:
            events.append(
                UserMessage(
                    index=len(events),
                    payload=MessagePayload(
                        content=message.get("content"),
                        name=message.get("name"),
                        source_role=role,
                    ),
                )
            )

    if error is not None:
        events.append(
            ErrorEvent(
                index=len(events),
                payload=ErrorPayload(
                    error_type=type(error).__name__,
                    message=str(error),
                ),
            )
        )
        return events

    payload = _plain(response)
    for choice in payload.get("choices", []) if isinstance(payload, dict) else []:
        message = choice.get("message", {})
        for call in message.get("tool_calls") or []:
            function = call.get("function", {})
            events.append(
                ToolCall(
                    index=len(events),
                    payload=ToolCallPayload(
                        name=function.get("name", "unknown_tool"),
                        arguments=_arguments(function.get("arguments", {})),
                        call_id=call.get("id"),
                    ),
                )
            )
        if message.get("content") is not None or message.get("refusal") is not None:
            events.append(
                AssistantMessage(
                    index=len(events),
                    payload=MessagePayload(
                        content=message.get("content"),
                        refusal=bool(message.get("refusal")),
                    ),
                )
            )
    return events


def create_openai_client() -> Any:
    """Construct an OpenAI client for the explicitly live drift workflow."""

    from openai import OpenAI

    return OpenAI()


def create_groq_client() -> Any:
    """Construct an OpenAI-compatible client pointed at Groq's API."""

    from openai import OpenAI

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is required for Groq drift")
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
