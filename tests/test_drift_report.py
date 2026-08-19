from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ferric.drift import DriftProviderError, classify_drift, load_dotenv, run_drift
from ferric.report import render_drift_report, write_drift_report
from ferric.schema import (
    AssistantMessage,
    Cassette,
    DriftClassification,
    DriftDimension,
    MessagePayload,
    ToolCall,
)
from ferric.store import CassetteStore


def test_load_dotenv_reads_local_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Load a quoted local key without requiring python-dotenv."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    path = tmp_path / ".env"
    path.write_text(
        "# local credentials\nOPENAI_API_KEY='local-test-key'\n",
        encoding="utf-8",
    )
    assert load_dotenv(path) == path
    assert os.environ["OPENAI_API_KEY"] == "local-test-key"


def test_load_dotenv_preserves_existing_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep a shell credential ahead of a value in the local file."""

    monkeypatch.setenv("ANTHROPIC_API_KEY", "shell-key")
    path = tmp_path / ".env"
    path.write_text("ANTHROPIC_API_KEY=file-key\n", encoding="utf-8")
    load_dotenv(path)
    assert os.environ["ANTHROPIC_API_KEY"] == "shell-key"


def test_drift_classifies_unchanged(sample_cassette: Cassette) -> None:
    result = classify_drift(sample_cassette, sample_cassette.events, 17)
    assert result.classification is DriftClassification.UNCHANGED
    assert result.tokens_spent == 17


def test_drift_classifies_reworded(sample_cassette: Cassette) -> None:
    events = [event.model_copy(deep=True) for event in sample_cassette.events]
    assistant = events[-1]
    assert isinstance(assistant, AssistantMessage)
    events[-1] = assistant.model_copy(
        update={
            "payload": MessagePayload(
                content={
                    "month": "March 2026",
                    "rows": 1842,
                    "anomalies": 3,
                    "review_id": "local-review-17",
                }
            )
        }
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


def test_drift_classifies_recursive_integer_to_string_as_schema(
    sample_cassette: Cassette,
) -> None:
    events = [event.model_copy(deep=True) for event in sample_cassette.events]
    assistant = events[-1]
    assert isinstance(assistant, AssistantMessage)
    content = dict(assistant.payload.content)
    content["anomalies"] = "3"
    events[-1] = assistant.model_copy(
        update={"payload": MessagePayload(content=content)}
    )
    result = classify_drift(sample_cassette, events, 0)
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


class _FakeDriftEndpoint:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "deterministic target response",
                    }
                }
            ],
            "usage": {"total_tokens": 10},
        }


def test_run_drift_uses_explicit_provider_and_skips_mcp(cassette_dir: Path) -> None:
    endpoint = _FakeDriftEndpoint()
    client = SimpleNamespace(chat=SimpleNamespace(completions=endpoint))
    run = run_drift(
        CassetteStore(cassette_dir),
        "gpt-local-target",
        target_provider="openai",
        client=client,
    )
    assert run.target_provider == "openai"
    assert len(run.results) == 3
    assert len(run.skipped) == 1
    assert "MCP tool exchange" in run.skipped[0].reason
    assert run.tokens_spent == 30
    assert len(endpoint.calls) == 3
    assert all(call["model"] == "gpt-local-target" for call in endpoint.calls)


def test_run_drift_supports_groq_openai_compatible_endpoint(cassette_dir: Path) -> None:
    """Use the Groq target label with the same chat completion shape."""

    endpoint = _FakeDriftEndpoint()
    client = SimpleNamespace(chat=SimpleNamespace(completions=endpoint))
    run = run_drift(
        CassetteStore(cassette_dir),
        "llama-3.3-70b-versatile",
        target_provider="groq",
        client=client,
    )
    assert run.target_provider == "groq"
    assert len(run.results) == 3
    assert run.tokens_spent == 30


def test_run_drift_converts_missing_sdk_to_domain_error(
    cassette_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_sdk() -> Any:
        raise ImportError("openai is absent")

    monkeypatch.setattr("ferric.drift.create_openai_client", missing_sdk)
    with pytest.raises(DriftProviderError, match="openai.*extra"):
        run_drift(
            CassetteStore(cassette_dir),
            "gpt-local-target",
            target_provider="openai",
        )
