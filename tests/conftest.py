from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from ferric.adapters.openai import normalise_openai
from ferric.matcher import request_fingerprint
from ferric.schema import Cassette
from ferric.store import build_cassette


@pytest.fixture
def golden_dir() -> Path:
    return Path(__file__).with_name("goldens")


@pytest.fixture
def cassette_dir() -> Path:
    return Path(__file__).with_name("cassettes")


@pytest.fixture
def openai_payload(golden_dir: Path) -> dict[str, Any]:
    return json.loads((golden_dir / "openai_input.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_cassette(openai_payload: dict[str, Any]) -> Cassette:
    request = openai_payload["request"]
    events = normalise_openai(request, openai_payload["response"])
    return build_cassette(
        provider="openai",
        model=request["model"],
        fingerprint=request_fingerprint(
            request["model"], request["messages"], request["tools"]
        ),
        latency_ms=12,
        request=request,
        response=openai_payload["response"],
        response_kind="mapping",
        events=events,
        recorded_at=datetime(2026, 8, 17, tzinfo=UTC),
        provenance="Deterministic local test fixture.",
    )
