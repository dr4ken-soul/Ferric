from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from ferric.adapters.anthropic import normalise_anthropic
from ferric.adapters.mcp import normalise_mcp
from ferric.adapters.openai import normalise_openai


@pytest.mark.parametrize(
    ("provider", "normaliser"),
    [
        ("openai", normalise_openai),
        ("anthropic", normalise_anthropic),
        ("mcp", normalise_mcp),
    ],
)
def test_adapter_matches_independent_golden(
    golden_dir: Path,
    provider: str,
    normaliser: Any,
) -> None:
    fixture = json.loads(
        (golden_dir / f"{provider}_input.json").read_text(encoding="utf-8")
    )
    expected = json.loads(
        (golden_dir / f"{provider}_expected.json").read_text(encoding="utf-8")
    )
    observed = [
        event.model_dump(mode="json")
        for event in normaliser(fixture["request"], fixture["response"])
    ]
    assert observed == expected


@pytest.mark.parametrize(
    ("normaliser", "case_payload"),
    [
        (normalise_openai, {"messages": [{"role": "user", "content": "hello"}]}),
        (normalise_anthropic, {"messages": [{"role": "user", "content": "hello"}]}),
        (normalise_mcp, {"method": "local_tool", "params": {}}),
    ],
)
def test_adapter_records_provider_error(
    normaliser: Any, case_payload: dict[str, Any]
) -> None:
    events = normaliser(case_payload, error=RuntimeError("local deterministic failure"))
    assert events[-1].role.value == "error"
    assert events[-1].payload.error_type == "RuntimeError"


def test_importing_ferric_does_not_import_provider_sdks() -> None:
    assert "openai" not in sys.modules
    assert "anthropic" not in sys.modules


def test_openai_invalid_argument_json_is_retained_safely() -> None:
    request = {
        "messages": [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call-local",
                        "function": {"name": "tool", "arguments": "not json"},
                    }
                ],
            }
        ]
    }
    events = normalise_openai(request, {"choices": []})
    assert events[0].payload.arguments == {"_raw": "not json"}


def test_standard_mcp_tools_call_matches_golden(golden_dir: Path) -> None:
    fixture = json.loads(
        (golden_dir / "mcp_standard_input.json").read_text(encoding="utf-8")
    )
    expected = json.loads(
        (golden_dir / "mcp_standard_expected.json").read_text(encoding="utf-8")
    )
    observed = [
        event.model_dump(mode="json")
        for event in normalise_mcp(fixture["request"], fixture["response"])
    ]
    assert observed == expected
