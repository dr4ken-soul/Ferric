from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from ferric.schema import (
    Cassette,
    DriftClassification,
    DriftResult,
    MessagePayload,
    UserMessage,
    calculate_content_id,
)


def test_event_rejects_negative_index() -> None:
    with pytest.raises(ValidationError):
        UserMessage(index=-1, payload=MessagePayload(content="hello"))


def test_event_rejects_unknown_payload_field() -> None:
    with pytest.raises(ValidationError):
        MessagePayload.model_validate({"content": "hello", "unknown": True})


def test_cassette_rejects_non_monotonic_events(sample_cassette: Cassette) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["events"][1]["index"] = 0
    data["id"] = calculate_content_id(
        [sample_cassette.events[0], sample_cassette.events[0]]
    )
    with pytest.raises(ValidationError, match="monotonic"):
        Cassette.model_validate(data)


def test_cassette_rejects_inconsistent_identifier(sample_cassette: Cassette) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["id"] = "0" * 64
    with pytest.raises(ValidationError, match="identifier"):
        Cassette.model_validate(data)


def test_cassette_requires_timezone(sample_cassette: Cassette) -> None:
    data = sample_cassette.model_dump()
    data["recorded_at"] = datetime(2026, 8, 17)
    with pytest.raises(ValidationError, match="timezone"):
        Cassette.model_validate(data)


def test_content_id_is_stable_across_serialisation(sample_cassette: Cassette) -> None:
    rebuilt = Cassette.model_validate_json(sample_cassette.model_dump_json(indent=4))
    assert calculate_content_id(rebuilt.events) == sample_cassette.id


def test_drift_result_requires_divergence_dimension(sample_cassette: Cassette) -> None:
    with pytest.raises(ValidationError, match="dimension"):
        DriftResult(
            cassette_id=sample_cassette.id,
            classification=DriftClassification.DIVERGED,
            baseline_events=sample_cassette.events,
            target_events=sample_cassette.events,
            tokens_spent=0,
        )


def test_drift_result_rejects_dimension_on_unchanged(sample_cassette: Cassette) -> None:
    with pytest.raises(ValidationError, match="only diverged"):
        DriftResult.model_validate(
            {
                "cassette_id": sample_cassette.id,
                "classification": "unchanged",
                "dimension": "refusal",
                "baseline_events": sample_cassette.events,
                "target_events": sample_cassette.events,
                "tokens_spent": 0,
            }
        )
