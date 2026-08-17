from __future__ import annotations

import json
from pathlib import Path

import pytest

from ferric.redact import RedactionRule, Redactor
from ferric.schema import Cassette, calculate_integrity_hash_payload
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
    data["integrity_hash"] = calculate_integrity_hash_payload(data)
    cassette = Cassette.model_validate(data)
    written = CassetteStore(tmp_path).write(cassette)
    raw = (tmp_path / f"{written.id}.json").read_text(encoding="utf-8")
    assert secret not in raw
    assert any(record.rule_class == rule_class for record in written.redactions)


def test_redactor_applies_custom_rule(sample_cassette: Cassette) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["request"]["tenant"] = "tenant-private-42"
    data["integrity_hash"] = calculate_integrity_hash_payload(data)
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
    data["integrity_hash"] = calculate_integrity_hash_payload(data)
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteStoreError, match="unredacted email"):
        store.verify()


def test_redactor_catches_numeric_cards_and_sensitive_mapping_keys() -> None:
    findings = Redactor().find_sensitive(
        {
            "sk-local-key-name": "safe",
            "numeric_card": 4111111111111111,
        }
    )
    assert ("$.<key>", "api_key") in findings
    assert ("$.numeric_card", "card") in findings


def test_store_redacts_numeric_card_and_mapping_key(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    data = sample_cassette.model_dump(mode="json")
    data["request"]["sk-local-mapping-key"] = "safe"
    data["request"]["numeric_card"] = 4111111111111111
    data["integrity_hash"] = calculate_integrity_hash_payload(data)
    written = CassetteStore(tmp_path).write(Cassette.model_validate(data))
    raw = (tmp_path / f"{written.id}.json").read_text(encoding="utf-8")
    assert "sk-local-mapping-key" not in raw
    assert "4111111111111111" not in raw
    assert {record.rule_class for record in written.redactions} >= {
        "api_key",
        "card",
    }


def test_verify_rejects_empty_library(tmp_path: Path) -> None:
    with pytest.raises(CassetteStoreError, match="library is empty"):
        CassetteStore(tmp_path).verify()


def test_integrity_hash_detects_replay_critical_tampering(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    written = CassetteStore(tmp_path).write(sample_cassette)
    path = tmp_path / f"{written.id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["response"]["choices"][0]["message"]["content"] = "tampered"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteStoreError, match="integrity_hash"):
        CassetteStore(tmp_path).verify()


def test_verify_rejects_missing_integrity_hash(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    written = CassetteStore(tmp_path).write(sample_cassette)
    path = tmp_path / f"{written.id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["integrity_hash"]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteStoreError, match="integrity_hash"):
        CassetteStore(tmp_path).verify()


def test_integrity_hash_covers_assertion_evidence(
    cassette_dir: Path, tmp_path: Path
) -> None:
    source = next(
        cassette
        for cassette in CassetteStore(cassette_dir).verify()
        if cassette.assertions
    )
    written = CassetteStore(tmp_path).write(source)
    path = tmp_path / f"{written.id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["assertions"][0]["message"] = "tampered evidence"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteStoreError, match="integrity_hash"):
        CassetteStore(tmp_path).verify()


def test_verify_reports_located_pydantic_path(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    written = CassetteStore(tmp_path).write(sample_cassette)
    path = tmp_path / f"{written.id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["events"][0]["payload"]["content"]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteStoreError, match=r"events\.0"):
        CassetteStore(tmp_path).verify()


def test_verify_aggregates_unsafe_findings_without_values(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    written = CassetteStore(tmp_path).write(sample_cassette)
    path = tmp_path / f"{written.id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["request"]["first"] = "operator@example.test"
    data["request"]["second"] = 4111111111111111
    data["integrity_hash"] = calculate_integrity_hash_payload(data)
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteStoreError) as failure:
        CassetteStore(tmp_path).verify()
    message = str(failure.value)
    assert "unredacted email" in message and "unredacted card" in message
    assert "operator@example.test" not in message
    assert "4111111111111111" not in message
