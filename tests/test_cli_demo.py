from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

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
    assert "Verified 3 cassette(s)" in result.stdout


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
    assert {row["cassette"] for row in rows} == cassette_ids
    assert sum(row["tokens"] for row in rows) == 614
