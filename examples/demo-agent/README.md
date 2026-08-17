# Ferric Local Demo Agent

This fixture is a deterministic local MCP-shaped recording. It exercises `read_ledger`, `flag_anomalies` and `prepare_review` through Ferric's MCP normaliser. It is not captured Kiro production traffic and does not claim access to a Kiro production session.

Run it offline:

```bash
FERRIC_MODE=replay python examples/demo-agent/agent.py
```

No provider key or network connection is used.
