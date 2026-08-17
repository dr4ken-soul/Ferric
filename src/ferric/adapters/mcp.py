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

    params = request.get("params")
    standard_params = params if request.get("method") == "tools/call" else None
    name = str(
        request.get("name")
        or (standard_params.get("name") if isinstance(standard_params, dict) else None)
        or request.get("method")
        or "unknown_tool"
    )
    arguments = (
        standard_params.get("arguments", {})
        if isinstance(standard_params, dict)
        else request.get("arguments") or params or {}
    )
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
        plain_response = (
            response.model_dump(mode="json")
            if response is not None and hasattr(response, "model_dump")
            else response
        )
        result = (
            plain_response.get("result")
            if isinstance(plain_response, dict) and "result" in plain_response
            else plain_response
        )
        error_payload = (
            plain_response.get("error") if isinstance(plain_response, dict) else None
        )
        content = error_payload if error_payload is not None else result
        is_error = error_payload is not None or (
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
