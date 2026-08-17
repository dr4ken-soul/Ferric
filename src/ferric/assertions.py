"""Behavioural assertions for Ferric cassettes."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from ferric.schema import Cassette, EventRole


class FerricAssertionError(AssertionError):
    """Report a safe, actionable cassette assertion failure."""


def _cassette_label(cassette: Cassette) -> str:
    return f"cassette {cassette.id}"


def _tool_calls(cassette: Cassette) -> list[Any]:
    return [
        event.payload for event in cassette.events if event.role is EventRole.TOOL_CALL
    ]


def assert_tool_sequence(cassette: Cassette, expected: Sequence[str]) -> None:
    """Assert ordered tool names and report the first divergent index."""

    observed = [call.name for call in _tool_calls(cassette)]
    expected_list = list(expected)
    if observed == expected_list:
        return
    first = next(
        (
            index
            for index in range(max(len(expected_list), len(observed)))
            if index >= len(expected_list)
            or index >= len(observed)
            or expected_list[index] != observed[index]
        ),
        0,
    )
    raise FerricAssertionError(
        f"{_cassette_label(cassette)} tool sequence diverged at index {first}; "
        f"expected {expected_list!r}, observed {observed!r}"
    )


def _lookup_path(value: Any, path: str) -> tuple[bool, Any]:
    current = value
    for part in path.split(".") if path else []:
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def assert_tool_arguments(
    cassette: Cassette,
    tool_name: str,
    expected: Mapping[str, Any],
    occurrence: int = 0,
) -> None:
    """Assert only declared critical fields for one tool call."""

    calls = [call for call in _tool_calls(cassette) if call.name == tool_name]
    if occurrence >= len(calls):
        raise FerricAssertionError(
            f"{_cassette_label(cassette)} missing tool {tool_name!r} occurrence "
            f"{occurrence}; expected {dict(expected)!r}, observed no call"
        )
    observed = calls[occurrence].arguments
    for path, expected_value in expected.items():
        found, observed_value = _lookup_path(observed, path)
        if not found or observed_value != expected_value:
            safe_observed = "(absent)" if not found else repr(observed_value)
            raise FerricAssertionError(
                f"{_cassette_label(cassette)} tool {tool_name!r} field {path!r} "
                f"did not match; expected {expected_value!r}, observed {safe_observed}"
            )


def _response_value(cassette: Cassette) -> Any:
    assistants = [
        event.payload.content
        for event in cassette.events
        if event.role is EventRole.ASSISTANT
    ]
    if not assistants:
        return None
    value = assistants[-1]
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _schema_error(value: Any, schema: Mapping[str, Any], path: str) -> str | None:
    expected_type = schema.get("type")
    type_matches = {
        "object": isinstance(value, Mapping),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }
    if expected_type in type_matches and not type_matches[expected_type]:
        return f"{path}: expected {expected_type}, observed {type(value).__name__}"
    if "enum" in schema and value not in schema["enum"]:
        return f"{path}: value is not in the declared enum"
    if isinstance(value, Mapping):
        for required in schema.get("required", []):
            if required not in value:
                return f"{path}.{required}: required property is missing"
        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                failure = _schema_error(value[key], child_schema, f"{path}.{key}")
                if failure:
                    return failure
    if isinstance(value, list) and isinstance(schema.get("items"), Mapping):
        for index, child in enumerate(value):
            failure = _schema_error(child, schema["items"], f"{path}[{index}]")
            if failure:
                return failure
    return None


def assert_response_schema(cassette: Cassette, schema: Mapping[str, Any]) -> None:
    """Validate structured assistant output and report its failing JSON path."""

    value = _response_value(cassette)
    failure = _schema_error(value, schema, "$")
    if failure:
        raise FerricAssertionError(
            f"{_cassette_label(cassette)} response schema failed at {failure}; "
            f"expected {dict(schema)!r}, observed {value!r}"
        )


def assert_refusal(cassette: Cassette, expected: bool = True) -> None:
    """Assert whether the recorded assistant response was a refusal."""

    observed = any(
        event.payload.refusal
        for event in cassette.events
        if event.role is EventRole.ASSISTANT
    )
    if observed != expected:
        raise FerricAssertionError(
            f"{_cassette_label(cassette)} refusal mismatch; expected {expected!r}, "
            f"observed {observed!r}"
        )


def assert_no_leakage(
    cassette: Cassette,
    patterns: Mapping[str, str | re.Pattern[str]],
) -> None:
    """Assert declared patterns do not appear in outbound event payloads."""

    compiled = {
        name: re.compile(pattern) if isinstance(pattern, str) else pattern
        for name, pattern in patterns.items()
    }
    for path, value in _walk_strings(cassette.request, "$.request"):
        for name, pattern in compiled.items():
            if pattern.search(value):
                raise FerricAssertionError(
                    f"{_cassette_label(cassette)} leakage {name!r} in outbound "
                    f"request at {path}; expected no match, observed {name!r}"
                )
    for event in cassette.events:
        if event.role not in {EventRole.USER, EventRole.TOOL_RESULT}:
            continue
        payload = event.payload.model_dump(mode="json")
        for path, value in _walk_strings(payload):
            for name, pattern in compiled.items():
                if pattern.search(value):
                    raise FerricAssertionError(
                        f"{_cassette_label(cassette)} leakage {name!r} in event "
                        f"{event.index} at {path}; expected no match, observed {name!r}"
                    )


def _walk_strings(value: Any, path: str = "$") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, Mapping):
        result: list[tuple[str, str]] = []
        for key, child in value.items():
            result.extend(_walk_strings(child, f"{path}.{key}"))
        return result
    if isinstance(value, list):
        result = []
        for index, child in enumerate(value):
            result.extend(_walk_strings(child, f"{path}[{index}]"))
        return result
    return []
