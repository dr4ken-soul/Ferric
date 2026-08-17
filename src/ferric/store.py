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
)


class CassetteStoreError(RuntimeError):
    """Report a corrupt or inconsistent cassette store."""


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

    return Cassette.model_validate(
        {
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
    )


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
        self._atomic_json(path, safe_cassette.model_dump(mode="json"))
        manifest = self._manifest_from_disk()
        self._atomic_json(self.manifest_path, manifest.model_dump(mode="json"))
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
        for cassette in cassettes:
            findings = self.redactor.find_sensitive(cassette.model_dump(mode="json"))
            if findings:
                path, rule_class = findings[0]
                raise CassetteStoreError(
                    f"{cassette.id}.json:{path}: unredacted {rule_class} value"
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
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as error:
            raise CassetteStoreError(
                f"{path}: invalid cassette: {type(error).__name__}"
            ) from error

    def _read_manifest(self) -> Manifest:
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return Manifest.model_validate(data)
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as error:
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
