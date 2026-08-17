from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ferric.drift import classify_drift
from ferric.report import render_drift_report, write_drift_report
from ferric.schema import (
    AssistantMessage,
    Cassette,
    DriftClassification,
    DriftDimension,
    MessagePayload,
    ToolCall,
)


def test_drift_classifies_unchanged(sample_cassette: Cassette) -> None:
    result = classify_drift(sample_cassette, sample_cassette.events, 17)
    assert result.classification is DriftClassification.UNCHANGED
    assert result.tokens_spent == 17


def test_drift_classifies_reworded(sample_cassette: Cassette) -> None:
    events = [event.model_copy(deep=True) for event in sample_cassette.events]
    assistant = events[-1]
    assert isinstance(assistant, AssistantMessage)
    events[-1] = assistant.model_copy(
        update={"payload": MessagePayload(content={"summary": "wording moved"})}
    )
    result = classify_drift(sample_cassette, events, 23)
    assert result.classification is DriftClassification.REWORDED


def test_drift_classifies_tool_order(sample_cassette: Cassette) -> None:
    events = [event.model_copy(deep=True) for event in sample_cassette.events]
    indexes = [
        index for index, event in enumerate(events) if isinstance(event, ToolCall)
    ]
    first_payload = events[indexes[0]].payload
    second_payload = events[indexes[1]].payload
    events[indexes[0]] = events[indexes[0]].model_copy(
        update={"payload": second_payload}
    )
    events[indexes[1]] = events[indexes[1]].model_copy(
        update={"payload": first_payload}
    )
    result = classify_drift(sample_cassette, events, 29)
    assert result.dimension is DriftDimension.TOOL_ORDER


def test_drift_classifies_tool_selection(sample_cassette: Cassette) -> None:
    events = [event.model_copy(deep=True) for event in sample_cassette.events]
    index = next(
        index for index, event in enumerate(events) if isinstance(event, ToolCall)
    )
    call = events[index]
    events[index] = call.model_copy(
        update={"payload": call.payload.model_copy(update={"name": "different_tool"})}
    )
    result = classify_drift(sample_cassette, events, 31)
    assert result.dimension is DriftDimension.TOOL_SELECTION


def test_drift_classifies_schema_validity(sample_cassette: Cassette) -> None:
    events = [event.model_copy(deep=True) for event in sample_cassette.events]
    assistant = events[-1]
    assert isinstance(assistant, AssistantMessage)
    events[-1] = assistant.model_copy(
        update={"payload": MessagePayload(content="not structured output")}
    )
    result = classify_drift(sample_cassette, events, 37)
    assert result.dimension is DriftDimension.SCHEMA_VALIDITY


def test_drift_classifies_refusal(sample_cassette: Cassette) -> None:
    events = [event.model_copy(deep=True) for event in sample_cassette.events]
    assistant = events[-1]
    assert isinstance(assistant, AssistantMessage)
    events[-1] = assistant.model_copy(
        update={"payload": assistant.payload.model_copy(update={"refusal": True})}
    )
    result = classify_drift(sample_cassette, events, 41)
    assert result.dimension is DriftDimension.REFUSAL


def test_report_is_self_contained(sample_cassette: Cassette) -> None:
    result = classify_drift(sample_cassette, sample_cassette.events, 17)
    document = render_drift_report(
        [result],
        baseline_model="local-a",
        target_model="local-b",
        generated_at=datetime(2026, 8, 17, tzinfo=UTC),
    )
    lowered = document.casefold()
    assert "<style>" in document and "<script>" in document
    assert "http://" not in lowered and "https://" not in lowered
    assert "src=" not in lowered and "href=" not in lowered
    assert "@media(max-width:767px)" in document
    assert "@media print" in document


def test_report_escapes_embedded_script(sample_cassette: Cassette) -> None:
    events = [event.model_copy(deep=True) for event in sample_cassette.events]
    assistant = events[-1]
    assert isinstance(assistant, AssistantMessage)
    events[-1] = assistant.model_copy(
        update={"payload": MessagePayload(content="</script><script>unsafe()</script>")}
    )
    result = classify_drift(sample_cassette, events, 0)
    document = render_drift_report(
        [result], baseline_model="local", target_model="local"
    )
    assert "</script><script>unsafe()" not in document
    assert "<\\/script>" in document


def test_report_writes_atomically(tmp_path: Path, sample_cassette: Cassette) -> None:
    result = classify_drift(sample_cassette, sample_cassette.events, 17)
    path = write_drift_report(
        tmp_path / "report.html",
        [result],
        baseline_model="local-a",
        target_model="local-b",
    )
    assert path.read_text(encoding="utf-8").startswith("<!doctype html>")
