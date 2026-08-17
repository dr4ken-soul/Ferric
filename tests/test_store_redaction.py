from __future__ import annotations

import json
from pathlib import Path

import pytest

from ferric.redact import RedactionRule, Redactor
from ferric.schema import Cassette
from ferric.store import CassetteStore, CassetteStoreError, content_hash


def test_store_round_trip(tmp_path: Path, sample_cassette: Cassette) -> None:
    store = CassetteStore(tmp_path)
    written = store.write(sample_cassette)
    assert store.read(written.id) == written


def test_store_repeated_write_has_stable_identifier(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    store = CassetteStore(tmp_path)
    first = store.write(sample_cassette)
    second = store.write(sample_cassette)
    assert first.id == second.id == content_hash(first.events)
    assert len(store.list()) == 1


def test_store_manifest_updates_after_delete(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    store = CassetteStore(tmp_path)
    written = store.write(sample_cassette)
    store.delete(written.id[:12])
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == {"entries": []}


def test_store_detects_manifest_inconsistency(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    store = CassetteStore(tmp_path)
    store.write(sample_cassette)
    (tmp_path / "manifest.json").write_text('{"entries": []}', encoding="utf-8")
    with pytest.raises(CassetteStoreError, match="manifest"):
        store.list()


@pytest.mark.parametrize(
    ("secret", "rule_class"),
    [
        ("sk-localSecret123", "api_key"),
        ("Bearer local.token.value", "bearer_token"),
        ("ledger.operator@example.test", "email"),
        ("4111 1111 1111 1111", "card"),
    ],
)
def test_write_path_redacts_built_in_secrets(
    tmp_path: Path,
    sample_cassette: Cassette,
    secret: str,
    rule_class: str,
) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["events"][0]["payload"]["content"] = f"value {secret}"
    from pydantic import TypeAdapter

    from ferric.schema import Event, calculate_content_id

    events = TypeAdapter(list[Event]).validate_python(data["events"])
    data["id"] = calculate_content_id(events)
    cassette = Cassette.model_validate(data)
    written = CassetteStore(tmp_path).write(cassette)
    raw = (tmp_path / f"{written.id}.json").read_text(encoding="utf-8")
    assert secret not in raw
    assert any(record.rule_class == rule_class for record in written.redactions)


def test_redactor_applies_custom_rule(sample_cassette: Cassette) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["request"]["tenant"] = "tenant-private-42"
    from ferric.schema import Cassette as CassetteModel

    cassette = CassetteModel.model_validate(data)
    redactor = Redactor((RedactionRule.from_pattern("tenant", r"tenant-private-\d+"),))
    safe = redactor.redact_cassette(cassette)
    assert safe.request["tenant"] == "[REDACTED:tenant]"
    assert any(record.field_path == "$.request.tenant" for record in safe.redactions)


def test_verify_rejects_unredacted_file(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    store = CassetteStore(tmp_path)
    written = store.write(sample_cassette)
    path = tmp_path / f"{written.id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["request"]["unrelated"] = "email operator@example.test"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteStoreError, match="unredacted email"):
        store.verify()
