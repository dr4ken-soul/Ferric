from __future__ import annotations

from pathlib import Path

import pytest

from ferric.matcher import (
    UnmatchedRequestError,
    fingerprint_distance,
    match_cassette,
    request_fingerprint,
)
from ferric.schema import Cassette
from ferric.store import CassetteStore


def test_fingerprint_excludes_volatile_fields() -> None:
    first = request_fingerprint(
        "local-model",
        [{"role": "user", "content": "hello", "id": "one", "timestamp": 1}],
        [],
    )
    second = request_fingerprint(
        "local-model",
        [{"timestamp": 99, "content": "hello", "role": "user", "id": "two"}],
        [],
    )
    assert first == second


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
