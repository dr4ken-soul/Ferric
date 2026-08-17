"""Run Ferric's deterministic local three-tool MCP demonstration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ferric.schema import EventRole
from ferric.store import CassetteStore


class DemoAgent:
    """Replay three locally normalised MCP tool exchanges."""

    def __init__(self, cassette_dir: Path) -> None:
        """Initialise the agent from a committed cassette directory."""

        self.store = CassetteStore(cassette_dir)

    def run(self) -> dict[str, Any]:
        """Replay the local tools and return the final review summary."""

        if os.environ.get("FERRIC_MODE", "replay") != "replay":
            raise RuntimeError("the demo supports replay mode only")
        results: dict[str, Any] = {}
        for cassette in self.store.verify():
            call = next(
                event for event in cassette.events if event.role is EventRole.TOOL_CALL
            )
            result = next(
                event
                for event in cassette.events
                if event.role is EventRole.TOOL_RESULT
            )
            results[call.payload.name] = result.payload.content
        expected = {"read_ledger", "flag_anomalies", "prepare_review"}
        if set(results) != expected:
            raise RuntimeError(
                f"expected three local tools, observed {sorted(results)}"
            )
        return results


def main() -> None:
    """Print a compact result from the offline demo agent."""

    cassette_dir = Path(__file__).with_name("cassettes")
    results = DemoAgent(cassette_dir).run()
    print("Ferric replayed 3 deterministic local MCP tool calls.")
    print(f"Tools: {', '.join(sorted(results))}")
    print("Provenance: local demo fixture, not Kiro production capture.")


if __name__ == "__main__":
    main()
