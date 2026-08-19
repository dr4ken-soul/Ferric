"""Classify model drift and isolate the explicitly live provider path."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from ferric.adapters.anthropic import create_anthropic_client, normalise_anthropic
from ferric.adapters.openai import create_openai_client, normalise_openai
from ferric.schema import (
    Cassette,
    DriftClassification,
    DriftDimension,
    DriftResult,
    DriftRun,
    DriftSkipped,
    Event,
    EventRole,
)
from ferric.store import CassetteStore


class DriftProviderError(RuntimeError):
    """Report a provider failure during an explicitly requested drift run."""


def load_dotenv(path: Path | None = None) -> Path | None:
    """Load simple local environment entries without replacing shell values."""

    candidate = path or Path.cwd() / ".env"
    if not candidate.is_file():
        return None
    for raw_line in candidate.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key.isidentifier():
            os.environ.setdefault(key, value)
    return candidate


def _tool_names(events: list[Event]) -> list[str]:
    return [event.payload.name for event in events if event.role is EventRole.TOOL_CALL]


def _assistant_shape(events: list[Event]) -> list[tuple[str, bool]]:
    return [
        (
            event.role.value,
            event.payload.refusal if event.role is EventRole.ASSISTANT else False,
        )
        for event in events
        if event.role in {EventRole.ASSISTANT, EventRole.USER, EventRole.TOOL_RESULT}
    ]


def _json_value(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped.startswith(("{", "[")):
            return value
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return value
    return value


def _json_shape(value: Any) -> Any:
    value = _json_value(value)
    if isinstance(value, dict):
        return {key: _json_shape(child) for key, child in sorted(value.items())}
    if isinstance(value, list):
        return [_json_shape(child) for child in value]
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value is None:
        return "null"
    return "string"


def _schema_dimension(baseline: list[Event], target: list[Event]) -> bool:
    baseline_values = [
        event.payload.content for event in baseline if event.role is EventRole.ASSISTANT
    ]
    target_values = [
        event.payload.content for event in target if event.role is EventRole.ASSISTANT
    ]
    return bool(baseline_values and target_values) and (
        len(baseline_values) != len(target_values)
        or any(
            _json_shape(value) != _json_shape(other)
            for value, other in zip(baseline_values, target_values, strict=False)
        )
    )


def classify_drift(
    cassette: Cassette,
    target_events: list[Event],
    tokens_spent: int,
) -> DriftResult:
    """Classify one target event list as unchanged, reworded or diverged."""

    baseline = cassette.events
    if [event.model_dump(mode="json") for event in baseline] == [
        event.model_dump(mode="json") for event in target_events
    ]:
        classification = DriftClassification.UNCHANGED
        dimension = None
    elif _tool_names(baseline) != _tool_names(target_events):
        classification = DriftClassification.DIVERGED
        dimension = (
            DriftDimension.TOOL_ORDER
            if sorted(_tool_names(baseline)) == sorted(_tool_names(target_events))
            else DriftDimension.TOOL_SELECTION
        )
    elif _schema_dimension(baseline, target_events):
        classification = DriftClassification.DIVERGED
        dimension = DriftDimension.SCHEMA_VALIDITY
    elif any(
        event.payload.refusal != target.payload.refusal
        for event, target in zip(
            [item for item in baseline if item.role is EventRole.ASSISTANT],
            [item for item in target_events if item.role is EventRole.ASSISTANT],
            strict=False,
        )
    ):
        classification = DriftClassification.DIVERGED
        dimension = DriftDimension.REFUSAL
    elif _assistant_shape(baseline) == _assistant_shape(target_events):
        classification = DriftClassification.REWORDED
        dimension = None
    else:
        classification = DriftClassification.DIVERGED
        dimension = DriftDimension.SCHEMA_VALIDITY
    return DriftResult(
        cassette_id=cassette.id,
        classification=classification,
        dimension=dimension,
        baseline_events=baseline,
        target_events=target_events,
        tokens_spent=tokens_spent,
    )


def _token_count(response: Any) -> int:
    usage = response.get("usage") if isinstance(response, dict) else None
    if usage is None and hasattr(response, "usage"):
        usage = response.usage
    if usage is not None and hasattr(usage, "model_dump"):
        usage = usage.model_dump(mode="json")
    if isinstance(usage, dict):
        return int(
            usage.get(
                "total_tokens",
                usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            )
        )
    return 0


def infer_target_provider(target_model: str) -> Literal["openai", "anthropic"]:
    """Infer a supported target provider from a model identifier."""

    lowered = target_model.casefold()
    return "anthropic" if "claude" in lowered else "openai"


def _target_request(
    cassette: Cassette,
    target_model: str,
    target_provider: Literal["openai", "anthropic"],
) -> dict[str, Any]:
    request: dict[str, Any] = dict(cassette.request)
    request.pop("_positional_args", None)
    request["model"] = target_model
    if cassette.provider == target_provider:
        return request
    messages = request.get("messages", [])
    if target_provider == "openai":
        system = request.pop("system", None)
        converted: list[dict[str, Any]] = []
        if system is not None:
            converted.append({"role": "system", "content": system})
        for message in messages if isinstance(messages, list) else []:
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if isinstance(content, list):
                text = "\n".join(
                    str(block.get("text"))
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
                content = text
            converted.append({"role": message.get("role", "user"), "content": content})
        request["messages"] = converted
        request.pop("max_tokens", None)
        tools = request.get("tools")
        if isinstance(tools, list):
            request["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {}),
                    },
                }
                for tool in tools
                if isinstance(tool, dict) and "name" in tool
            ]
    else:
        converted = []
        system_parts: list[Any] = []
        for message in messages if isinstance(messages, list) else []:
            if not isinstance(message, dict):
                continue
            role = message.get("role", "user")
            if role == "system":
                system_parts.append(message.get("content"))
            elif role in {"user", "assistant"}:
                converted.append({"role": role, "content": message.get("content")})
        if system_parts:
            request["system"] = "\n".join(str(part) for part in system_parts)
        request["messages"] = converted
        request.setdefault("max_tokens", 1024)
        tools = request.get("tools")
        if isinstance(tools, list):
            request["tools"] = [
                {
                    "name": function.get("name"),
                    "description": function.get("description", ""),
                    "input_schema": function.get("parameters", {}),
                }
                for tool in tools
                if isinstance(tool, dict)
                and isinstance((function := tool.get("function")), dict)
            ]
    return request


def _live_call(
    cassette: Cassette,
    target_model: str,
    target_provider: Literal["openai", "anthropic"],
    client: Any | None = None,
) -> tuple[list[Event], int]:
    request = _target_request(cassette, target_model, target_provider)
    if target_provider == "openai":
        try:
            target_client = client if client is not None else create_openai_client()
        except ImportError as error:
            raise DriftProviderError(
                "OpenAI drift requires the 'openai' extra"
            ) from error
        try:
            response = target_client.chat.completions.create(**request)
        except BaseException as error:
            raise DriftProviderError(
                f"{cassette.id}: target provider call failed"
            ) from error
        return normalise_openai(request, response), _token_count(response)
    if target_provider == "anthropic":
        try:
            target_client = client if client is not None else create_anthropic_client()
        except ImportError as error:
            raise DriftProviderError(
                "Anthropic drift requires the 'anthropic' extra"
            ) from error
        try:
            response = target_client.messages.create(**request)
        except BaseException as error:
            raise DriftProviderError(
                f"{cassette.id}: target provider call failed"
            ) from error
        return normalise_anthropic(request, response), _token_count(response)
    raise DriftProviderError(f"unsupported target provider {target_provider!r}")


def run_drift(
    store: CassetteStore,
    target_model: str,
    *,
    target_provider: Literal["openai", "anthropic"] | None = None,
    client: Any | None = None,
) -> DriftRun:
    """Call one target provider and skip unsupported MCP baselines honestly."""

    selected = target_provider or infer_target_provider(target_model)
    results: list[DriftResult] = []
    skipped: list[DriftSkipped] = []
    for cassette in store.verify():
        if cassette.provider == "mcp":
            skipped.append(
                DriftSkipped(
                    cassette_id=cassette.id,
                    reason="MCP tool exchange cannot be submitted to a model provider",
                )
            )
            continue
        target_events, tokens = _live_call(cassette, target_model, selected, client)
        results.append(classify_drift(cassette, target_events, tokens))
    return DriftRun(
        target_provider=selected,
        target_model=target_model,
        results=results,
        skipped=skipped,
    )
