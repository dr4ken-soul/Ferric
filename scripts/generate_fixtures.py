"""Generate deterministic local cassettes and the committed sample report."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue

from ferric.adapters.anthropic import normalise_anthropic
from ferric.adapters.mcp import normalise_mcp
from ferric.adapters.openai import normalise_openai
from ferric.drift import classify_drift
from ferric.matcher import request_fingerprint
from ferric.report import write_drift_report
from ferric.schema import (
    AssertionEvidence,
    AssertionFamily,
    AssertionStatus,
    AssistantMessage,
    Cassette,
    DriftEvidence,
    DriftResult,
    Event,
    EventRole,
    MessagePayload,
    ReplayEvidence,
    ToolCall,
)
from ferric.store import CassetteStore, build_cassette

ROOT = Path(__file__).resolve().parents[1]
RECORDED_AT = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
PROVENANCE = (
    "Deterministic local Ferric demo fixture. Not provider or Kiro production traffic."
)
DRIFT_PROVENANCE = (
    "Deterministic local drift classification. Not a live provider capture."
)
REPLAY_PROVENANCE = (
    "Deterministic local replay duration for reproducible evidence. "
    "No provider transport was constructed."
)


def _load(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((ROOT / "tests" / "goldens" / name).read_text(encoding="utf-8")),
    )


def _local_drift_results(cassettes: list[Cassette]) -> list[DriftResult]:
    openai, anthropic, mcp = cassettes
    changed = [event.model_copy(deep=True) for event in openai.events]
    call_indexes = [
        index for index, event in enumerate(changed) if isinstance(event, ToolCall)
    ]
    first, second = call_indexes[0], call_indexes[1]
    first_payload = changed[first].payload.model_copy(deep=True)
    second_payload = changed[second].payload.model_copy(deep=True)
    changed[first] = changed[first].model_copy(update={"payload": second_payload})
    changed[second] = changed[second].model_copy(update={"payload": first_payload})

    reworded = [event.model_copy(deep=True) for event in anthropic.events]
    last = reworded[-1]
    if isinstance(last, AssistantMessage):
        reworded[-1] = last.model_copy(
            update={
                "payload": MessagePayload(
                    content="Three anomalies require manual review."
                )
            }
        )
    return [
        classify_drift(openai, changed, 493),
        classify_drift(anthropic, reworded, 121),
        classify_drift(mcp, mcp.events, 0),
    ]


def _assertion_evidence() -> list[AssertionEvidence]:
    expected: list[JsonValue] = [
        "read_ledger",
        "flag_anomalies",
        "prepare_review",
    ]
    observed: list[JsonValue] = [
        "flag_anomalies",
        "read_ledger",
        "prepare_review",
    ]
    return [
        AssertionEvidence(
            family=AssertionFamily.SEQUENCE,
            status=AssertionStatus.PASS,
            message="tool sequence matched the recorded baseline",
            expected=expected,
            observed=expected,
        ),
        AssertionEvidence(
            family=AssertionFamily.SEQUENCE,
            status=AssertionStatus.FAIL,
            message="tool order diverged at index 0",
            expected=expected,
            observed=observed,
        ),
        AssertionEvidence(
            family=AssertionFamily.ARGUMENTS,
            status=AssertionStatus.PASS,
            message="critical month and threshold fields matched",
        ),
        AssertionEvidence(
            family=AssertionFamily.SCHEMA,
            status=AssertionStatus.PASS,
            message="structured anomaly result matched the local schema",
        ),
        AssertionEvidence(
            family=AssertionFamily.LEAKAGE,
            status=AssertionStatus.PASS,
            message="0 declared secret matches across outbound fields",
        ),
    ]


def _behavioural_drift_events(events: list[Event]) -> list[Event]:
    return [event for event in events if event.role is not EventRole.TOOL_RESULT]


def _write_primary_cassettes() -> list[Cassette]:
    store = CassetteStore(ROOT / "tests" / "cassettes")
    openai = _load("openai_input.json")
    anthropic = _load("anthropic_input.json")
    mcp = _load("mcp_input.json")
    drafts: list[Cassette] = []
    for provider, payload, normaliser, latency in (
        ("openai", openai, normalise_openai, 184),
        ("anthropic", anthropic, normalise_anthropic, 211),
        ("mcp", mcp, normalise_mcp, 3),
    ):
        request = payload["request"]
        model = request.get("model", "mcp-local")
        messages = request.get("messages", [request])
        tools = request.get("tools", [{"name": request.get("method")}])
        events = normaliser(request, payload["response"])
        drafts.append(
            build_cassette(
                provider=provider,
                model=model,
                fingerprint=request_fingerprint(model, messages, tools),
                latency_ms=latency,
                request=request,
                response=payload["response"],
                response_kind="mapping",
                events=events,
                recorded_at=RECORDED_AT,
                provenance=PROVENANCE,
            )
        )
    results = _local_drift_results(drafts)
    records: list[Cassette] = []
    for cassette, result in zip(drafts, results, strict=True):
        data = cassette.model_dump(mode="json")
        data["drift"] = DriftEvidence(
            classification=result.classification,
            dimension=result.dimension,
            baseline_events=_behavioural_drift_events(result.baseline_events),
            target_events=_behavioural_drift_events(result.target_events),
            tokens_spent=result.tokens_spent,
            provenance=DRIFT_PROVENANCE,
        ).model_dump(mode="json")
        if cassette.provider == "openai":
            data["assertions"] = [
                evidence.model_dump(mode="json") for evidence in _assertion_evidence()
            ]
            data["replay"] = ReplayEvidence(
                network_calls=0,
                tokens=0,
                duration_ms=7,
                provenance=REPLAY_PROVENANCE,
            ).model_dump(mode="json")
        records.append(store.write(Cassette.model_validate(data)))
    return records


def _write_demo_cassettes() -> None:
    store = CassetteStore(ROOT / "examples" / "demo-agent" / "cassettes")
    fixtures: tuple[tuple[str, dict[str, JsonValue], JsonValue], ...] = (
        ("read_ledger", {"month": "2026-03"}, {"rows": 1842}),
        ("flag_anomalies", {"threshold": 0.04}, {"count": 3}),
        (
            "prepare_review",
            {"month": "2026-03", "count": 3},
            {"review_id": "local-review-17"},
        ),
    )
    for index, (name, arguments, response) in enumerate(fixtures, 1):
        request: dict[str, JsonValue] = {
            "id": f"demo-{index}",
            "method": name,
            "params": arguments,
        }
        events = normalise_mcp(request, response)
        store.write(
            build_cassette(
                provider="mcp",
                model="mcp-local",
                fingerprint=request_fingerprint(
                    "mcp-local", [request], [{"name": name}]
                ),
                latency_ms=index,
                request=request,
                response=response,
                response_kind="mapping",
                events=events,
                recorded_at=RECORDED_AT,
                provenance=PROVENANCE,
            )
        )


def _write_sample_report(cassettes: list[Cassette]) -> None:
    results = _local_drift_results(cassettes)
    write_drift_report(
        ROOT / "examples" / "sample-drift-report.html",
        results,
        baseline_model="recorded local fixtures",
        target_model="deterministic local candidate",
        generated_at=RECORDED_AT,
    )


def main() -> None:
    """Regenerate all deterministic local evidence files."""

    cassettes = _write_primary_cassettes()
    _write_demo_cassettes()
    _write_sample_report(cassettes)


if __name__ == "__main__":
    main()
