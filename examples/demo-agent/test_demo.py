"""Verify the deterministic local demo agent."""

from pathlib import Path

from agent import DemoAgent


def test_demo_agent_replays_three_tools() -> None:
    results = DemoAgent(Path(__file__).with_name("cassettes")).run()
    assert set(results) == {"read_ledger", "flag_anomalies", "prepare_review"}
