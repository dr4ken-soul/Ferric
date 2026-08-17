"""Persist redacted cassettes and a consistent manifest."""

from __future__ import annotations

import builtins
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import JsonValue, ValidationError

from ferric.redact import RedactionRule, Redactor
from ferric.schema import (
    AssertionEvidence,
    Cassette,
    DriftEvidence,
    Event,
    Manifest,
    ManifestEntry,
    RedactionRecord,
    ReplayEvidence,
    calculate_content_id,
    calculate_integrity_hash_payload,
)


class CassetteStoreError(RuntimeError):
    """Report a corrupt or inconsistent cassette store."""


def _validation_locations(error: ValidationError) -> str:
    locations: list[str] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        if not location and "integrity hash" in item["msg"]:
            location = "integrity_hash"
        elif not location and "identifier" in item["msg"]:
            location = "id"
        locations.append(location or "$")
    return ", ".join(locations)


def default_cassette_dir() -> Path:
    """Return the configured cassette directory or the project default."""

    configured = os.environ.get("FERRIC_CASSETTE_DIR")
    return Path(configured) if configured else Path("tests/cassettes")


def content_hash(events: list[Event]) -> str:
    """Return the stable content identifier for an event list."""

    return calculate_content_id(events)


def build_cassette(
    *,
    provider: str,
    model: str,
    fingerprint: str,
    latency_ms: int,
    request: dict[str, JsonValue],
    response: JsonValue | None,
    response_kind: str,
    events: list[Event],
    response_json: str | None = None,
    recorded_at: datetime | None = None,
    redactions: list[RedactionRecord] | None = None,
    provenance: str | None = None,
    assertions: list[AssertionEvidence] | None = None,
    drift: DriftEvidence | None = None,
    replay: ReplayEvidence | None = None,
) -> Cassette:
    """Construct a validated cassette from normalised interaction data."""

    data: dict[str, Any] = {
        "id": content_hash(events),
        "provider": provider,
        "model": model,
        "recorded_at": recorded_at or datetime.now(UTC),
        "fingerprint": fingerprint,
        "latency_ms": latency_ms,
        "request": request,
        "response": response,
        "response_kind": response_kind,
        "response_json": response_json,
        "events": [event.model_dump(mode="json") for event in events],
        "redactions": redactions or [],
        "provenance": provenance,
        "assertions": assertions or [],
        "drift": drift,
        "replay": replay,
    }
    data["integrity_hash"] = calculate_integrity_hash_payload(data)
    return Cassette.model_validate(data)


class CassetteStore:
    """Read and atomically write a directory of cassette JSON files."""

    def __init__(
        self,
        root: Path | str | None = None,
        custom_rules: tuple[RedactionRule, ...] = (),
    ) -> None:
        """Initialise a store without creating files until the first write."""

        self.root = Path(root) if root is not None else default_cassette_dir()
        self.manifest_path = self.root / "manifest.json"
        self.redactor = Redactor(custom_rules)

    def write(self, cassette: Cassette) -> Cassette:
        """Redact and atomically persist a cassette and its manifest."""

        safe_cassette = self.redactor.redact_cassette(cassette)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{safe_cassette.id}.json"
        previous_cassette = path.read_bytes() if path.exists() else None
        previous_manifest = (
            self.manifest_path.read_bytes() if self.manifest_path.exists() else None
        )
        try:
            self._atomic_json(path, safe_cassette.model_dump(mode="json"))
            manifest = self._manifest_from_disk()
            self._atomic_json(self.manifest_path, manifest.model_dump(mode="json"))
        except BaseException:
            self._restore(path, previous_cassette)
            self._restore(self.manifest_path, previous_manifest)
            raise
        return safe_cassette

    def read(self, cassette_id: str) -> Cassette:
        """Read a cassette by full identifier or unambiguous prefix."""

        matches = [
            path for path in self._cassette_paths() if path.stem.startswith(cassette_id)
        ]
        if not matches:
            raise CassetteStoreError(f"cassette {cassette_id!r} was not found")
        if len(matches) > 1:
            raise CassetteStoreError(f"cassette prefix {cassette_id!r} is ambiguous")
        return self._read_path(matches[0])

    def list(self) -> builtins.list[Cassette]:
        """Return every cassette after checking manifest consistency."""

        cassettes = [self._read_path(path) for path in self._cassette_paths()]
        expected = self._manifest_for(cassettes)
        if self.manifest_path.exists():
            actual = self._read_manifest()
            if actual != expected:
                raise CassetteStoreError("manifest does not match cassette files")
        elif cassettes:
            raise CassetteStoreError("manifest is missing")
        return cassettes

    def delete(self, cassette_id: str) -> None:
        """Delete one cassette and update the manifest atomically."""

        cassette = self.read(cassette_id)
        path = self.root / f"{cassette.id}.json"
        path.unlink()
        manifest = self._manifest_from_disk()
        self._atomic_json(self.manifest_path, manifest.model_dump(mode="json"))

    def verify(self) -> builtins.list[Cassette]:
        """Validate schema, identifiers, manifest and redaction for the store."""

        cassettes = self.list()
        if not cassettes:
            raise CassetteStoreError("cassette library is empty")
        unsafe: list[str] = []
        for cassette in cassettes:
            findings = self.redactor.find_sensitive(cassette.model_dump(mode="json"))
            unsafe.extend(
                f"{cassette.id}.json:{path}: unredacted {rule_class} value"
                for path, rule_class in findings
            )
        if unsafe:
            raise CassetteStoreError(
                "redaction verification failed:\n" + "\n".join(unsafe)
            )
        return cassettes

    def _cassette_paths(self) -> builtins.list[Path]:
        if not self.root.exists():
            return []
        return sorted(
            path
            for path in self.root.glob("*.json")
            if path.name != self.manifest_path.name
        )

    def _read_path(self, path: Path) -> Cassette:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Cassette.model_validate(data)
        except ValidationError as error:
            locations = _validation_locations(error)
            raise CassetteStoreError(
                f"{path}: invalid cassette at {locations}"
            ) from error
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CassetteStoreError(
                f"{path}: invalid cassette: {type(error).__name__}"
            ) from error

    def _read_manifest(self) -> Manifest:
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return Manifest.model_validate(data)
        except ValidationError as error:
            locations = _validation_locations(error)
            raise CassetteStoreError(
                f"{self.manifest_path}: invalid manifest at {locations}"
            ) from error
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CassetteStoreError(
                f"{self.manifest_path}: invalid manifest: {type(error).__name__}"
            ) from error

    def _manifest_from_disk(self) -> Manifest:
        return self._manifest_for(
            [self._read_path(path) for path in self._cassette_paths()]
        )

    @staticmethod
    def _manifest_for(cassettes: builtins.list[Cassette]) -> Manifest:
        entries = [
            ManifestEntry(
                id=cassette.id,
                provider=cassette.provider,
                model=cassette.model,
                recorded_at=cassette.recorded_at,
                event_count=len(cassette.events),
            )
            for cassette in sorted(cassettes, key=lambda item: item.id)
        ]
        return Manifest(entries=entries)

    @staticmethod
    def _atomic_json(path: Path, data: dict[str, Any]) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            text=True,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(data, handle, ensure_ascii=True, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        except BaseException:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _restore(path: Path, content: bytes | None) -> None:
        if content is None:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            return
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".restore",
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        except BaseException:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
