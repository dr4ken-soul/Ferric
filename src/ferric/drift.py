"""Classify model drift and isolate the explicitly live provider path."""

from __future__ import annotations

import json
from typing import Any

from ferric.adapters.anthropic import create_anthropic_client, normalise_anthropic
from ferric.adapters.openai import create_openai_client, normalise_openai
from ferric.schema import (
    Cassette,
    DriftClassification,
    DriftDimension,
    DriftResult,
    Event,
    EventRole,
)
from ferric.store import CassetteStore


class DriftProviderError(RuntimeError):
    """Report a provider failure during an explicitly requested drift run."""


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


def _is_json_assistant(value: Any) -> bool:
    if not isinstance(value, str):
        return isinstance(value, (dict, list))
    try:
        json.loads(value)
    except json.JSONDecodeError:
        return False
    return True


def _schema_dimension(baseline: list[Event], target: list[Event]) -> bool:
    baseline_values = [
        event.payload.content for event in baseline if event.role is EventRole.ASSISTANT
    ]
    target_values = [
        event.payload.content for event in target if event.role is EventRole.ASSISTANT
    ]
    return bool(baseline_values and target_values) and any(
        _is_json_assistant(value) != _is_json_assistant(other)
        for value, other in zip(baseline_values, target_values, strict=False)
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


def _live_call(cassette: Cassette, target_model: str) -> tuple[list[Event], int]:
    request = dict(cassette.request)
    request["model"] = target_model
    if cassette.provider == "openai":
        client = create_openai_client()
        try:
            response = client.chat.completions.create(**request)
        except BaseException as error:
            raise DriftProviderError(
                f"{cassette.id}: target provider call failed"
            ) from error
        return normalise_openai(request, response), _token_count(response)
    if cassette.provider == "anthropic":
        client = create_anthropic_client()
        try:
            response = client.messages.create(**request)
        except BaseException as error:
            raise DriftProviderError(
                f"{cassette.id}: target provider call failed"
            ) from error
        return normalise_anthropic(request, response), _token_count(response)
    raise DriftProviderError(
        f"{cassette.id}: MCP fixtures require a target MCP server and are not model drift inputs"
    )


def run_drift(store: CassetteStore, target_model: str) -> list[DriftResult]:
    """Call the selected live provider for every supported cassette."""

    results: list[DriftResult] = []
    for cassette in store.verify():
        if cassette.provider == "mcp":
            results.append(classify_drift(cassette, cassette.events, 0))
            continue
        target_events, tokens = _live_call(cassette, target_model)
        results.append(classify_drift(cassette, target_events, tokens))
    return results
