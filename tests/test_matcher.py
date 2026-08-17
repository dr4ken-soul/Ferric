from __future__ import annotations

from pathlib import Path

import pytest

from ferric.matcher import (
    UnmatchedRequestError,
    fingerprint_distance,
    match_cassette,
    normalise_request_value,
    request_fingerprint,
)
from ferric.schema import Cassette
from ferric.store import CassetteStore


def test_top_level_normalisation_excludes_transport_fields() -> None:
    first = normalise_request_value(
        {"request_id": "one", "timestamp": 1, "account": {"id": 8841}},
        top_level=True,
    )
    second = normalise_request_value(
        {"request_id": "two", "timestamp": 99, "account": {"id": 8841}},
        top_level=True,
    )
    assert first == second == {"account": {"id": 8841}}


def test_fingerprint_preserves_nested_business_identifiers() -> None:
    first = request_fingerprint(
        "local-model", [{"role": "user", "content": "hello", "id": "one"}], []
    )
    second = request_fingerprint(
        "local-model", [{"role": "user", "content": "hello", "id": "two"}], []
    )
    assert first != second


def test_fingerprint_includes_anthropic_system_content() -> None:
    first = request_fingerprint(
        "claude-local", [{"role": "user", "content": "hello"}], [], "system one"
    )
    second = request_fingerprint(
        "claude-local", [{"role": "user", "content": "hello"}], [], "system two"
    )
    assert first != second


def test_fingerprint_includes_model_messages_and_tools() -> None:
    baseline = request_fingerprint("model-a", [{"content": "hello"}], [{"name": "one"}])
    assert baseline != request_fingerprint(
        "model-b", [{"content": "hello"}], [{"name": "one"}]
    )
    assert baseline != request_fingerprint(
        "model-a", [{"content": "changed"}], [{"name": "one"}]
    )
    assert baseline != request_fingerprint(
        "model-a", [{"content": "hello"}], [{"name": "two"}]
    )


def test_fingerprint_distance_counts_bits() -> None:
    assert fingerprint_distance("0" * 64, "0" * 63 + "f") == 4


def test_exact_match_only(tmp_path: Path, sample_cassette: Cassette) -> None:
    store = CassetteStore(tmp_path)
    written = store.write(sample_cassette)
    assert match_cassette(store, written.fingerprint).id == written.id


def test_unmatched_request_reports_nearest_cassette(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    store = CassetteStore(tmp_path)
    written = store.write(sample_cassette)
    fingerprint = "0" * 64
    with pytest.raises(UnmatchedRequestError) as failure:
        match_cassette(store, fingerprint)
    message = str(failure.value)
    assert fingerprint in message
    assert written.id in message
    assert "fingerprint distance" in message


def test_unmatched_empty_store_is_actionable(tmp_path: Path) -> None:
    with pytest.raises(UnmatchedRequestError, match="store is empty"):
        match_cassette(CassetteStore(tmp_path), "0" * 64)
