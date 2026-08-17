"""Normalise Model Context Protocol tool calls and results."""

from __future__ import annotations

from typing import Any

from ferric.schema import (
    ErrorEvent,
    ErrorPayload,
    Event,
    ToolCall,
    ToolCallPayload,
    ToolResult,
    ToolResultPayload,
)


def normalise_mcp(
    request: dict[str, Any],
    response: Any | None = None,
    error: BaseException | None = None,
) -> list[Event]:
    """Convert one honest MCP tool exchange into typed events."""

    name = str(request.get("name") or request.get("method") or "unknown_tool")
    arguments = request.get("arguments") or request.get("params") or {}
    call_id = request.get("id")
    events: list[Event] = [
        ToolCall(
            index=0,
            payload=ToolCallPayload(
                name=name,
                arguments=arguments
                if isinstance(arguments, dict)
                else {"_value": arguments},
                call_id=str(call_id) if call_id is not None else None,
            ),
        )
    ]
    if error is not None:
        events.append(
            ErrorEvent(
                index=1,
                payload=ErrorPayload(
                    error_type=type(error).__name__,
                    message=str(error),
                ),
            )
        )
    else:
        content = (
            response.model_dump(mode="json")
            if response is not None and hasattr(response, "model_dump")
            else response
        )
        is_error = (
            bool(content.get("isError", False)) if isinstance(content, dict) else False
        )
        events.append(
            ToolResult(
                index=1,
                payload=ToolResultPayload(
                    content=content,
                    name=name,
                    call_id=str(call_id) if call_id is not None else None,
                    is_error=is_error,
                ),
            )
        )
    return events
