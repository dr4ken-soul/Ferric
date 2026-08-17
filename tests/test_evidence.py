from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ferric.redact import Redactor
from ferric.schema import (
    AssertionEvidence,
    Cassette,
    DriftClassification,
    DriftDimension,
    DriftEvidence,
    ReplayEvidence,
)
from ferric.store import CassetteStore


def _tool_names(events: list[Any]) -> list[str]:
    return [event.payload.name for event in events if event.role.value == "tool_call"]


def test_evidence_is_optional(sample_cassette: Cassette) -> None:
    assert sample_cassette.assertions == []
    assert sample_cassette.drift is None
    assert sample_cassette.replay is None


def test_evidence_does_not_change_content_identifier(sample_cassette: Cassette) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["assertions"] = [
        AssertionEvidence(
            family="sequence",
            status="pass",
            message="local sequence matched",
        ).model_dump(mode="json")
    ]
    data["replay"] = ReplayEvidence(
        network_calls=0,
        tokens=0,
        duration_ms=7,
        provenance="Deterministic local timing.",
    ).model_dump(mode="json")
    evidenced = Cassette.model_validate(data)
    assert evidenced.id == sample_cassette.id


def test_store_redacts_sensitive_evidence_before_disk(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["assertions"] = [
        AssertionEvidence(
            family="leakage",
            status="fail",
            message="unsafe address operator@example.test",
            location="$.request.messages[0]",
        ).model_dump(mode="json")
    ]
    cassette = Cassette.model_validate(data)
    written = CassetteStore(tmp_path).write(cassette)
    raw = (tmp_path / f"{written.id}.json").read_text(encoding="utf-8")
    assert "operator@example.test" not in raw
    assert "[REDACTED:email]" in raw
    assert any(
        record.field_path == "$.assertions[0].message" for record in written.redactions
    )


def test_assertion_evidence_rejects_unknown_family() -> None:
    with pytest.raises(ValidationError):
        AssertionEvidence.model_validate(
            {"family": "wording", "status": "pass", "message": "invalid"}
        )


def test_replay_evidence_rejects_negative_counts() -> None:
    with pytest.raises(ValidationError):
        ReplayEvidence(
            network_calls=-1,
            tokens=0,
            duration_ms=7,
            provenance="Deterministic local timing.",
        )


def test_drift_evidence_requires_dimension(sample_cassette: Cassette) -> None:
    with pytest.raises(ValidationError, match="requires a dimension"):
        DriftEvidence(
            classification=DriftClassification.DIVERGED,
            baseline_events=sample_cassette.events,
            target_events=sample_cassette.events,
            tokens_spent=0,
            provenance="Deterministic local classification.",
        )


def test_fixture_evidence_is_valid_and_safely_provenanced(cassette_dir: Path) -> None:
    cassettes = CassetteStore(cassette_dir).verify()
    assert {
        cassette.drift.classification for cassette in cassettes if cassette.drift
    } == {
        DriftClassification.UNCHANGED,
        DriftClassification.REWORDED,
        DriftClassification.DIVERGED,
    }
    for cassette in cassettes:
        assert cassette.drift is not None
        assert "Deterministic local drift classification" in cassette.drift.provenance
        assert "Not a live provider capture" in cassette.drift.provenance
        assert cassette.drift.baseline_events
        assert cassette.drift.target_events
        assert cassette.drift.tokens_spent >= 0
    assert (
        Redactor().find_sensitive(
            [cassette.model_dump(mode="json") for cassette in cassettes]
        )
        == []
    )


def test_fixture_contains_evidenced_tool_order_divergence(cassette_dir: Path) -> None:
    cassettes = CassetteStore(cassette_dir).verify()
    diverged = next(
        cassette
        for cassette in cassettes
        if cassette.drift
        and cassette.drift.classification is DriftClassification.DIVERGED
    )
    assert diverged.drift is not None
    assert diverged.drift.dimension is DriftDimension.TOOL_ORDER
    assert _tool_names(diverged.drift.baseline_events) == [
        "read_ledger",
        "flag_anomalies",
        "prepare_review",
    ]
    assert _tool_names(diverged.drift.target_events) == [
        "flag_anomalies",
        "read_ledger",
        "prepare_review",
    ]


def test_fixture_assertions_cover_every_family_and_sequence_failure(
    cassette_dir: Path,
) -> None:
    cassettes = CassetteStore(cassette_dir).verify()
    assertions = [item for cassette in cassettes for item in cassette.assertions]
    passing_families = {
        assertion.family.value
        for assertion in assertions
        if assertion.status.value == "pass"
    }
    assert passing_families == {"sequence", "arguments", "schema", "leakage"}
    failure = next(
        assertion
        for assertion in assertions
        if assertion.family.value == "sequence" and assertion.status.value == "fail"
    )
    assert failure.expected == [
        "read_ledger",
        "flag_anomalies",
        "prepare_review",
    ]
    assert failure.observed == [
        "flag_anomalies",
        "read_ledger",
        "prepare_review",
    ]


def test_fixture_replay_evidence_proves_local_zero_network(cassette_dir: Path) -> None:
    cassettes = CassetteStore(cassette_dir).verify()
    replay = next(cassette.replay for cassette in cassettes if cassette.replay)
    assert replay.network_calls == 0
    assert replay.tokens == 0
    assert replay.duration_ms == 7
    assert "Deterministic local replay duration" in replay.provenance
    assert "No provider transport was constructed" in replay.provenance


def test_fixture_shape_populates_site_generator_without_writing_web() -> None:
    root = Path(__file__).parents[1]
    namespace = runpy.run_path(str(root / "scripts" / "build_site_data.py"))
    read_cassettes = namespace["read_cassettes"]
    build_site_data = namespace["build_site_data"]
    assert callable(read_cassettes)
    assert callable(build_site_data)
    data = build_site_data(read_cassettes())
    assert data["replay"] == {
        "available": True,
        "networkCalls": 0,
        "tokens": 0,
        "durationMs": 7,
    }
    assert {row["classification"] for row in data["drift"]["rows"]} == {
        "unchanged",
        "reworded",
        "diverged",
    }
    assert data["drift"]["divergence"] == {
        "cassetteId": "7390ce",
        "dimension": "tool_order",
        "expected": "read_ledger -> flag_anomalies -> prepare_review",
        "observed": "flag_anomalies -> read_ledger -> prepare_review",
    }
    assert all(panel["available"] for panel in data["assertions"].values())
    assert json.dumps(data, ensure_ascii=True)
