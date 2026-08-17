"""Build typed website evidence through Ferric's validated cassette boundary."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASSETTE_DIR = ROOT / "tests" / "cassettes"
OUTPUT_PATH = ROOT / "web" / "src" / "data" / "cassettes.generated.ts"

sys.path.insert(0, str(ROOT / "src"))

from check_redaction import scan_paths  # noqa: E402
from ferric.schema import Cassette, calculate_integrity_hash_payload  # noqa: E402
from ferric.store import CassetteStore, CassetteStoreError  # noqa: E402


def read_cassettes() -> list[dict[str, Any]]:
    """Scan raw files, then validate schema, IDs, timestamps and manifest via the store."""
    if not CASSETTE_DIR.exists():
        return []
    cassette_paths = sorted(path for path in CASSETTE_DIR.glob("*.json") if path.name != "manifest.json")
    if not cassette_paths:
        return []
    violations, errors = scan_paths([CASSETTE_DIR])
    if violations or errors:
        detail = errors[0] if errors else f"{violations[0].path}:{violations[0].json_path}: sensitive data"
        raise ValueError(f"redaction validation failed: {detail}")
    with tempfile.TemporaryDirectory(prefix="ferric-site-data-") as temporary_name:
        validation_root = Path(temporary_name)
        manifest_payload = json.loads((CASSETTE_DIR / "manifest.json").read_text(encoding="utf-8"))
        (validation_root / "manifest.json").write_text(json.dumps(manifest_payload), encoding="utf-8")
        for source in cassette_paths:
            payload = json.loads(source.read_text(encoding="utf-8"))
            if "integrity_hash" in Cassette.model_fields and "integrity_hash" not in payload:
                payload["integrity_hash"] = calculate_integrity_hash_payload(payload)
            (validation_root / source.name).write_text(json.dumps(payload), encoding="utf-8")
        store = CassetteStore(validation_root)
        try:
            cassettes = store.verify()
            optional_integrity = getattr(store, "verify_integrity", None)
            if callable(optional_integrity):
                optional_integrity()
        except CassetteStoreError as error:
            raise ValueError(f"cassette store validation failed: {error}") from error
    return [
        {
            **cassette.model_dump(mode="json"),
            "source_path": str((CASSETTE_DIR / f"{cassette.id}.json").relative_to(ROOT)).replace("\\", "/"),
        }
        for cassette in cassettes
    ]


def compact_value(value: Any) -> str:
    """Serialise one validated value into deterministic display text."""
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def event_tool_name(event: dict[str, Any]) -> str | None:
    """Return a validated tool call name when present."""
    value = event["payload"].get("name")
    return value if isinstance(value, str) and value else None


def event_arguments(event: dict[str, Any]) -> dict[str, Any]:
    """Return a validated tool argument mapping when present."""
    value = event["payload"].get("arguments")
    return value if isinstance(value, dict) else {}


def event_summary(event: dict[str, Any]) -> str:
    """Build display text only from a validated event payload."""
    payload = event["payload"]
    if event["role"] == "tool_call":
        rendered = ", ".join(f"{key}={compact_value(value)}" for key, value in sorted(event_arguments(event).items()))
        return f"{event_tool_name(event) or 'tool_call'}({rendered})"
    for key in ("content", "message", "error_type"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value.replace("\n", " ").strip()
        if value is not None:
            return compact_value(value)
    return compact_value(payload)


def display_event(event: dict[str, Any]) -> dict[str, Any]:
    """Convert one validated event into the public display shape."""
    return {
        "index": event["index"],
        "role": event["role"],
        "summary": event_summary(event),
        "toolName": event_tool_name(event),
        "arguments": [
            {"name": key, "value": compact_value(value)}
            for key, value in sorted(event_arguments(event).items())
        ],
    }


def cassette_label(cassette_id: str) -> str:
    """Return the generated short content identifier used in compact panels."""
    return cassette_id[:6]


def unavailable_source() -> dict[str, Any]:
    """Return the evidence source shape used for an honest empty state."""
    return {"available": False, "label": "EVIDENCE UNAVAILABLE", "provenance": None, "source": None}


def evidence_source(cassette: dict[str, Any], provenance: Any = None) -> dict[str, Any]:
    """Preserve recorded provenance while labelling repository evidence as local fixture data."""
    return {
        "available": True,
        "label": "DETERMINISTIC LOCAL FIXTURE",
        "provenance": str(provenance or cassette.get("provenance") or "deterministic local fixture"),
        "source": cassette["source_path"],
    }


def explicit_assertions(cassettes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Extract only explicit Pydantic-validated assertion evidence."""
    result = {
        family: {"available": False, "lines": [], "evidenceSource": unavailable_source()}
        for family in ("sequence", "arguments", "schema", "leakage")
    }
    for cassette in cassettes:
        for assertion in cassette["assertions"]:
            family = assertion["family"]
            target = result[family]
            target["available"] = True
            if not target["evidenceSource"]["available"]:
                target["evidenceSource"] = evidence_source(cassette)
            target["lines"].append({
                "kind": assertion["status"],
                "text": f"cassette {cassette_label(cassette['id'])}  {assertion['message']}",
            })
            for label in ("expected", "observed", "pattern", "location"):
                value = assertion.get(label)
                if value is not None:
                    target["lines"].append({"kind": "detail", "text": f"{label}  {compact_value(value)}"})
    return result


def drift_tool_order(events: list[dict[str, Any]]) -> str:
    """Return generated tool order text from validated drift events."""
    return " -> ".join(name for event in events if (name := event_tool_name(event)))


def derive_drift(cassettes: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract explicit Pydantic-validated drift evidence and provenance."""
    rows: list[dict[str, Any]] = []
    divergence: dict[str, Any] | None = None
    source = unavailable_source()
    for cassette in cassettes:
        drift = cassette.get("drift")
        if drift is None:
            continue
        row = {
            "cassetteId": cassette_label(cassette["id"]),
            "eventCount": len(cassette["events"]),
            "classification": drift["classification"],
            "dimension": drift["dimension"],
        }
        rows.append(row)
        if not source["available"]:
            source = evidence_source(cassette, drift["provenance"])
        if drift["classification"] == "diverged" and divergence is None:
            source = evidence_source(cassette, drift["provenance"])
            divergence = {
                "cassetteId": row["cassetteId"],
                "dimension": drift["dimension"],
                "expected": drift_tool_order(drift["baseline_events"]),
                "observed": drift_tool_order(drift["target_events"]),
            }
    return {
        "available": bool(rows),
        "rows": rows,
        "divergence": divergence,
        "cassetteCount": len(rows),
        "regressionCount": sum(row["classification"] == "diverged" for row in rows),
        "evidenceSource": source,
    }


def build_site_data(cassettes: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the complete typed website contract from validated cassettes."""
    if not cassettes:
        return {
            "available": False,
            "hero": {"available": False, "cassetteId": None, "provider": None, "model": None, "eventCount": None, "events": [], "redactionCount": None, "evidenceSource": unavailable_source()},
            "library": {"available": False, "cassetteCount": None, "providerCount": None, "providers": [], "redactionRuleCount": None},
            "assertions": explicit_assertions([]),
            "drift": {"available": False, "rows": [], "divergence": None, "cassetteCount": None, "regressionCount": None, "evidenceSource": unavailable_source()},
            "replay": {"available": False, "networkCalls": None, "tokens": None, "durationMs": None, "evidenceSource": unavailable_source()},
        }
    featured = max(cassettes, key=lambda item: (len(item["events"]), item["id"]))
    providers = sorted({cassette["provider"] for cassette in cassettes})
    redaction_rules = sorted({
        record["rule_class"]
        for cassette in cassettes
        for record in cassette["redactions"]
    })
    replay = featured.get("replay")
    replay_data = {"available": False, "networkCalls": None, "tokens": None, "durationMs": None, "evidenceSource": unavailable_source()}
    if replay is not None:
        replay_data = {
            "available": True,
            "networkCalls": replay["network_calls"],
            "tokens": replay["tokens"],
            "durationMs": replay["duration_ms"],
            "evidenceSource": evidence_source(featured, replay["provenance"]),
        }
    return {
        "available": True,
        "hero": {
            "available": True,
            "cassetteId": cassette_label(featured["id"]),
            "provider": featured["provider"],
            "model": featured["model"],
            "eventCount": len(featured["events"]),
            "events": [display_event(event) for event in featured["events"]],
            "redactionCount": len(featured["redactions"]),
            "evidenceSource": evidence_source(featured),
        },
        "library": {
            "available": True,
            "cassetteCount": len(cassettes),
            "providerCount": len(providers),
            "providers": providers,
            "redactionRuleCount": len(redaction_rules),
        },
        "assertions": explicit_assertions(cassettes),
        "drift": derive_drift(cassettes),
        "replay": replay_data,
    }


def render_typescript(data: dict[str, Any]) -> str:
    """Render deterministic TypeScript with explicit public types."""
    payload = json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True)
    return f'''/* Generated by scripts/build_site_data.py. Do not edit. */
export type AssertionKind = 'pass' | 'fail' | 'detail'
export type AssertionFamily = 'sequence' | 'arguments' | 'schema' | 'leakage'

export interface DisplayEvent {{
  index: number
  role: string
  summary: string
  toolName: string | null
  arguments: Array<{{ name: string; value: string }}>
}}

export interface AssertionLine {{ kind: AssertionKind; text: string }}
export interface EvidenceSource {{ available: boolean; label: string; provenance: string | null; source: string | null }}

export interface SiteData {{
  available: boolean
  hero: {{ available: boolean; cassetteId: string | null; provider: string | null; model: string | null; eventCount: number | null; events: DisplayEvent[]; redactionCount: number | null; evidenceSource: EvidenceSource }}
  library: {{ available: boolean; cassetteCount: number | null; providerCount: number | null; providers: string[]; redactionRuleCount: number | null }}
  assertions: Record<AssertionFamily, {{ available: boolean; lines: AssertionLine[]; evidenceSource: EvidenceSource }}>
  drift: {{ available: boolean; rows: Array<{{ cassetteId: string; eventCount: number; classification: string; dimension: string | null }}>; divergence: {{ cassetteId: string; dimension: string; expected: string; observed: string }} | null; cassetteCount: number | null; regressionCount: number | null; evidenceSource: EvidenceSource }}
  replay: {{ available: boolean; networkCalls: number | null; tokens: number | null; durationMs: number | null; evidenceSource: EvidenceSource }}
}}

export const cassetteData: SiteData = {payload}
'''


def main() -> None:
    """Validate all evidence and write the generated TypeScript module."""
    data = build_site_data(read_cassettes())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_typescript(data), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
