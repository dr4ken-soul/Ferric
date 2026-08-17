"""Normalise Anthropic message requests and responses."""

from __future__ import annotations

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


def _append_content(events: list[Event], role: str, content: Any) -> None:
    blocks = (
        content if isinstance(content, list) else [{"type": "text", "text": content}]
    )
    for block in blocks:
        block_type = block.get("type", "text") if isinstance(block, dict) else "text"
        if block_type == "tool_use":
            events.append(
                ToolCall(
                    index=len(events),
                    payload=ToolCallPayload(
                        name=block.get("name", "unknown_tool"),
                        arguments=block.get("input", {}),
                        call_id=block.get("id"),
                    ),
                )
            )
        elif block_type == "tool_result":
            events.append(
                ToolResult(
                    index=len(events),
                    payload=ToolResultPayload(
                        content=block.get("content"),
                        call_id=block.get("tool_use_id"),
                        is_error=bool(block.get("is_error", False)),
                    ),
                )
            )
        else:
            text = block.get("text") if isinstance(block, dict) else block
            event_type = AssistantMessage if role == "assistant" else UserMessage
            events.append(
                event_type(
                    index=len(events),
                    payload=MessagePayload(
                        content=text,
                        source_role=None if role == "assistant" else role,
                    ),
                )
            )


def normalise_anthropic(
    request: dict[str, Any],
    response: Any | None = None,
    error: BaseException | None = None,
) -> list[Event]:
    """Convert one Anthropic messages exchange into typed events."""

    events: list[Event] = []
    system = request.get("system")
    if system is not None:
        _append_content(events, "system", _plain(system))
    for message in _plain(request.get("messages", [])):
        _append_content(events, message.get("role", "user"), message.get("content"))

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
    if isinstance(payload, dict):
        _append_content(events, "assistant", payload.get("content", []))
    return events


def create_anthropic_client() -> Any:
    """Construct an Anthropic client for the explicitly live drift workflow."""

    from anthropic import Anthropic

    return Anthropic()
