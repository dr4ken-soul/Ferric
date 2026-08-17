from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

from ferric.cli import app
from ferric.schema import Cassette
from ferric.store import CassetteStore

runner = CliRunner()


def test_cli_list_prints_validated_library(cassette_dir: Path) -> None:
    result = runner.invoke(app, ["list", "--cassette-dir", str(cassette_dir)])
    assert result.exit_code == 0
    assert "PROVIDER" in result.stdout
    assert "openai" in result.stdout
    assert "anthropic" in result.stdout
    assert "mcp" in result.stdout


def test_cli_verify_prints_exact_count(cassette_dir: Path) -> None:
    result = runner.invoke(app, ["verify", "--cassette-dir", str(cassette_dir)])
    assert result.exit_code == 0
    assert "Verified 4 cassette(s)" in result.stdout


def test_cli_list_handles_empty_library(tmp_path: Path) -> None:
    result = runner.invoke(app, ["list", "--cassette-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert result.stdout.strip() == "No cassettes found."


def test_cli_promote_invalid_trace_creates_nothing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    result = runner.invoke(
        app,
        [
            "promote",
            "missing",
            "--cassette-dir",
            str(source),
            "--output-dir",
            str(output),
        ],
    )
    assert result.exit_code != 0
    assert "was not found" in result.stdout
    assert not output.exists()


def test_cli_promote_generates_runnable_test(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    source = CassetteStore(tmp_path / "source")
    written = source.write(sample_cassette)
    output = tmp_path / "promoted"
    result = runner.invoke(
        app,
        [
            "promote",
            written.id[:12],
            "--cassette-dir",
            str(source.root),
            "--output-dir",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout
    test_file = output / f"test_promoted_{written.id[:12]}.py"
    assert test_file.exists()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q"],
        cwd=Path(__file__).parents[1],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "1 passed" in completed.stdout


def test_cli_promote_uses_recording_default_and_is_cwd_independent(
    tmp_path: Path,
    sample_cassette: Cassette,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = CassetteStore(tmp_path / "recordings")
    written = source.write(sample_cassette)
    monkeypatch.setenv("FERRIC_CASSETTE_DIR", str(source.root))
    output = tmp_path / "promoted"
    result = runner.invoke(
        app,
        ["promote", written.id[:12], "--output-dir", str(output)],
    )
    assert result.exit_code == 0, result.stdout
    test_file = output / f"test_promoted_{written.id[:12]}.py"
    generated = test_file.read_text(encoding="utf-8")
    assert "Path(__file__).parent.joinpath" in generated
    assert "BUILT_IN_RULES" in generated
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_cli_promote_rolls_back_cassette_when_test_write_fails(
    tmp_path: Path,
    sample_cassette: Cassette,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = CassetteStore(tmp_path / "source")
    written = source.write(sample_cassette)
    output = tmp_path / "output"

    def fail_replace(*_: object, **__: object) -> None:
        raise OSError("deterministic final write failure")

    monkeypatch.setattr("ferric.cli._replace", fail_replace)
    result = runner.invoke(
        app,
        [
            "promote",
            written.id,
            "--cassette-dir",
            str(source.root),
            "--output-dir",
            str(output),
        ],
    )
    assert result.exit_code != 0
    assert list((output / "cassettes").glob(f"{written.id}.json")) == []
    assert list(output.glob("test_promoted_*.py")) == []


def test_cli_verify_applies_repeatable_custom_rules(
    tmp_path: Path, sample_cassette: Cassette
) -> None:
    store = CassetteStore(tmp_path)
    written = store.write(sample_cassette)
    path = tmp_path / f"{written.id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["request"]["tenant"] = "tenant-private-42"
    from ferric.schema import calculate_integrity_hash_payload

    data["integrity_hash"] = calculate_integrity_hash_payload(data)
    path.write_text(json.dumps(data), encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "verify",
            "--cassette-dir",
            str(tmp_path),
            "--redact",
            r"tenant=tenant-private-\d+",
        ],
    )
    assert result.exit_code != 0
    assert "unredacted tenant" in result.stdout
    assert "tenant-private-42" not in result.stdout


def test_cli_verify_rejects_empty_library(tmp_path: Path) -> None:
    result = runner.invoke(app, ["verify", "--cassette-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "library is empty" in result.stdout


def test_cli_drift_reports_skipped_mcp_and_excludes_its_tokens(
    cassette_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []

    def create(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {
            "choices": [{"message": {"role": "assistant", "content": "local target"}}],
            "usage": {"total_tokens": 5},
        }

    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr("ferric.drift.create_openai_client", lambda: client)
    result = runner.invoke(
        app,
        [
            "drift",
            "--to",
            "gpt-local-target",
            "--provider",
            "openai",
            "--cassette-dir",
            str(cassette_dir),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "skipped 1" in result.stdout
    assert "tokens 15" in result.stdout
    assert "MCP tool exchange" in result.stdout
    assert len(calls) == 3


def test_demo_agent_runs_offline_in_under_two_minutes() -> None:
    root = Path(__file__).parents[1]
    script = root / "examples" / "demo-agent" / "agent.py"
    environment = {**os.environ, "FERRIC_MODE": "replay"}
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    elapsed = time.perf_counter() - started
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert elapsed < 120
    assert "3 deterministic local MCP tool calls" in completed.stdout
    assert "not Kiro production capture" in completed.stdout


def test_demo_cassettes_exercise_three_distinct_tools() -> None:
    root = Path(__file__).parents[1]
    store = CassetteStore(root / "examples" / "demo-agent" / "cassettes")
    names = {
        event.payload.name
        for cassette in store.verify()
        for event in cassette.events
        if event.role.value == "tool_call"
    }
    assert names == {"read_ledger", "flag_anomalies", "prepare_review"}


def test_sample_report_values_are_backed_by_committed_cassettes(
    cassette_dir: Path,
) -> None:
    root = Path(__file__).parents[1]
    report = (root / "examples" / "sample-drift-report.html").read_text(
        encoding="utf-8"
    )
    marker = '<script id="report-data" type="application/json">'
    payload = report.split(marker, 1)[1].split("</script>", 1)[0]
    rows = json.loads(payload)
    cassette_ids = {cassette.id for cassette in CassetteStore(cassette_dir).verify()}
    mcp_ids = {
        cassette.id
        for cassette in CassetteStore(cassette_dir).verify()
        if cassette.provider == "mcp"
    }
    assert {row["cassette"] for row in rows} == cassette_ids - mcp_ids
    assert sum(row["tokens"] for row in rows) == 614
