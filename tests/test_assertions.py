from __future__ import annotations

from typing import Any

import pytest

from ferric.assertions import (
    FerricAssertionError,
    assert_no_leakage,
    assert_refusal,
    assert_response_schema,
    assert_tool_arguments,
    assert_tool_sequence,
)
from ferric.schema import Cassette, calculate_content_id


def _changed(cassette: Cassette, change: Any) -> Cassette:
    data = cassette.model_dump(mode="json")
    change(data)
    from pydantic import TypeAdapter

    from ferric.schema import Event

    events = TypeAdapter(list[Event]).validate_python(data["events"])
    data["id"] = calculate_content_id(events)
    return Cassette.model_validate(data)


def test_tool_sequence_passes(sample_cassette: Cassette) -> None:
    assert_tool_sequence(
        sample_cassette, ["read_ledger", "flag_anomalies", "prepare_review"]
    )


def test_tool_sequence_reports_first_divergence(sample_cassette: Cassette) -> None:
    with pytest.raises(FerricAssertionError) as failure:
        assert_tool_sequence(sample_cassette, ["flag_anomalies", "read_ledger"])
    assert "index 0" in str(failure.value)
    assert sample_cassette.id in str(failure.value)
    assert "expected" in str(failure.value) and "observed" in str(failure.value)


def test_critical_arguments_ignore_undeclared_fields(sample_cassette: Cassette) -> None:
    assert_tool_arguments(sample_cassette, "prepare_review", {"month": "2026-03"})


def test_critical_arguments_support_nested_paths(sample_cassette: Cassette) -> None:
    nested = _changed(
        sample_cassette,
        lambda data: data["events"][2]["payload"]["arguments"].update(
            {"account": {"id": 8841}}
        ),
    )
    assert_tool_arguments(nested, "read_ledger", {"account.id": 8841})


def test_critical_arguments_report_missing_field(sample_cassette: Cassette) -> None:
    with pytest.raises(FerricAssertionError, match=r"observed \(absent\)"):
        assert_tool_arguments(sample_cassette, "flag_anomalies", {"account_id": 8841})


def test_response_schema_passes(sample_cassette: Cassette) -> None:
    assert_response_schema(
        sample_cassette,
        {
            "type": "object",
            "required": ["anomalies"],
            "properties": {"anomalies": {"type": "integer"}},
        },
    )


def test_response_schema_reports_nested_array_path(sample_cassette: Cassette) -> None:
    broken = _changed(
        sample_cassette,
        lambda data: data["events"][-1]["payload"].update(
            {"content": {"anomalies": [{"confidence": "high"}]}}
        ),
    )
    schema = {
        "type": "object",
        "properties": {
            "anomalies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"confidence": {"type": "number"}},
                },
            }
        },
    }
    with pytest.raises(FerricAssertionError, match=r"\$\.anomalies\[0\]\.confidence"):
        assert_response_schema(broken, schema)


def test_refusal_passes_when_not_expected(sample_cassette: Cassette) -> None:
    assert_refusal(sample_cassette, expected=False)


def test_refusal_reports_mismatch(sample_cassette: Cassette) -> None:
    with pytest.raises(FerricAssertionError, match="expected True, observed False"):
        assert_refusal(sample_cassette)


def test_no_leakage_passes(sample_cassette: Cassette) -> None:
    assert_no_leakage(sample_cassette, {"private_key": r"private-[0-9]+"})


def test_no_leakage_inspects_tool_definitions(sample_cassette: Cassette) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["request"]["tools"][0]["description"] = "private-739124"
    cassette = Cassette.model_validate(data)
    with pytest.raises(FerricAssertionError) as failure:
        assert_no_leakage(cassette, {"private_identifier": r"private-[0-9]+"})
    assert "$.request.tools[0].description" in str(failure.value)
    assert "739124" not in str(failure.value)


def test_no_leakage_reports_safe_location_not_value(sample_cassette: Cassette) -> None:
    leaked = _changed(
        sample_cassette,
        lambda data: data["events"][1]["payload"].update({"content": "private-739124"}),
    )
    with pytest.raises(FerricAssertionError) as failure:
        assert_no_leakage(leaked, {"private_identifier": r"private-[0-9]+"})
    message = str(failure.value)
    assert "event 1" in message and "$.content" in message
    assert "739124" not in message
