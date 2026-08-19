# How Ferric Was Built

Ferric was specified before its Python engine was committed. This document maps the Kiro requirements to tasks, implementation, tests, hooks and the actual four-commit history at the time of writing.

## Source trail

The Kiro artefacts are:

- [Requirements](../.kiro/specs/ferric-core/requirements.md), six user-facing requirements with acceptance criteria
- [Design](../.kiro/specs/ferric-core/design.md), boundaries, flows and verification strategy
- [Tasks](../.kiro/specs/ferric-core/tasks.md), nineteen dependency-ordered tasks linked to criteria
- [Offline guard](../.kiro/hooks/offline-guard.json)
- [Adapter golden tests](../.kiro/hooks/golden-tests.json)
- [Cassette redaction gate](../.kiro/hooks/redaction-gate.json)
- [Specification drift check](../.kiro/hooks/spec-drift.json)

The task file still contains unchecked boxes. The implementation and tests provide evidence for much of it, but the unchecked list is not rewritten here as a completed ledger. Requirement 5 live-provider validation and parts of Requirement 6 release validation remain incomplete.

## Requirement map

| Requirement | Kiro tasks | Implementation | Tests and artefacts | Guard |
|---|---|---|---|---|
| 1. Transparent capture | 2, 3, 5, 6, 8, 19 | [`schema.py`](../src/ferric/schema.py), [`store.py`](../src/ferric/store.py), [`wrapper.py`](../src/ferric/wrapper.py), [`openai.py`](../src/ferric/adapters/openai.py), [`anthropic.py`](../src/ferric/adapters/anthropic.py) | [`test_schema.py`](../tests/test_schema.py), [`test_store_redaction.py`](../tests/test_store_redaction.py), [`test_adapters.py`](../tests/test_adapters.py), [`test_wrapper.py`](../tests/test_wrapper.py) | Adapter golden tests rerun schema and normaliser checks after contract edits |
| 2. Hermetic replay | 1, 3, 9, 14, 19 | [`matcher.py`](../src/ferric/matcher.py), [`wrapper.py`](../src/ferric/wrapper.py), [`store.py`](../src/ferric/store.py) | [`test_matcher.py`](../tests/test_matcher.py) proves exact matching; [`test_wrapper.py`](../tests/test_wrapper.py) blocks `socket.socket` and provider calls, covers misses and repeated replay | Offline guard rejects known network and provider imports from default tests |
| 3. Safe promotion and redaction | 2, 4, 11, 14, 19 | [`redact.py`](../src/ferric/redact.py), [`store.py`](../src/ferric/store.py), [`cli.py`](../src/ferric/cli.py) | [`test_store_redaction.py`](../tests/test_store_redaction.py), [`test_cli_demo.py`](../tests/test_cli_demo.py), committed redacted cassettes under [`tests/cassettes`](../tests/cassettes) | Cassette redaction gate scans JSON without printing matched values |
| 4. Behavioural assertions | 4, 10, 17, 19 | [`assertions.py`](../src/ferric/assertions.py), evidence models in [`schema.py`](../src/ferric/schema.py) | [`test_assertions.py`](../tests/test_assertions.py) covers sequence, critical arguments, schema, leakage and refusal; [`test_evidence.py`](../tests/test_evidence.py) validates committed evidence for all four public families | Specification drift check asks for criteria and evidence at a task boundary |
| 5. Model drift reporting | 1, 12, 13, 19 | [`drift.py`](../src/ferric/drift.py), [`report.py`](../src/ferric/report.py), drift command in [`cli.py`](../src/ferric/cli.py) | [`test_drift_report.py`](../tests/test_drift_report.py) covers offline classification and self-contained HTML; [`sample-drift-report.html`](../examples/sample-drift-report.html) is deterministic local evidence | Offline guard keeps live tests outside the default suite; specification drift check covers evidence claims |
| 6. Verifiable delivery | 1, 7, 14 to 19 | [`agent.py`](../examples/demo-agent/agent.py), [`generate_fixtures.py`](../scripts/generate_fixtures.py), [`build_site_data.py`](../scripts/build_site_data.py), [`App.tsx`](../web/src/App.tsx), [`DocsPage.tsx`](../web/src/pages/DocsPage.tsx) | [`test_cli_demo.py`](../tests/test_cli_demo.py), [`test_evidence.py`](../tests/test_evidence.py), [`test_demo.py`](../examples/demo-agent/test_demo.py), this document and the [README](../README.md) | All four hook definitions address delivery invariants, but the final release task is not complete |

## What is implemented

Tasks 2 to 13 have direct Python modules and focused tests. Task 14 has a three-tool replay fixture, but it is deterministic local MCP-shaped data rather than Kiro production traffic. Tasks 15 to 17 have a cassette-driven web implementation and `npm run build` succeeds. Task 18 includes the web docs route and these repository documents. Task 19 is not complete because no clean external machine result, live drift run, demo video or final submission capture exists.

The committed sample report was generated from three local drift fixtures by [`scripts/generate_fixtures.py`](../scripts/generate_fixtures.py). It deliberately supplies one unchanged event set, one reworded event set and one tool-order change. The 614-token total is fixture metadata. It is not a live provider bill or capture.

## Commit history

| Commit | Evidence added | Requirement and task effect |
|---|---|---|
| `149bea7` | Kiro steering, requirements, design, nineteen tasks, four hooks and the two guard scripts | Established Tasks 1 to 19 and the offline, golden, redaction and specification evidence boundaries before application code |
| `60b9eda` | Python package, adapters, wrapper, matcher, store, assertions, CLI, drift classifier, report generator, tests and deterministic fixtures | Added the main implementation evidence for Requirements 1 to 5 and the local part of Requirement 6, chiefly Tasks 2 to 14 |
| `a8dd624` | Validated assertion, replay and drift evidence models plus evidence tests and regenerated cassettes | Made local provenance and displayed evidence machine-validated for Tasks 12, 14 and 15 |
| `bf914d8` | Store construction preserves provenance, assertions, drift and replay metadata | Fixed the write boundary so Requirement 6 evidence survives cassette construction |
| `6774678` | Hermetic replay hardening, numeric and key redaction, integrity hashes, standard MCP JSON-RPC, keyless replay and drift tests | Closed review findings across Requirements 2 to 5 and expanded the verification suite to 111 tests |
| `bb143bd` | Cassette-derived landing page, docs route, report evidence view, static-host routing and frontend checks | Added the web implementation for Requirements 4 and 6 |
| `6b405e9` | Excluded generated web dependencies from Git | Kept the public repository source-only and reproducible with `npm ci` |

`6b405e9` is the current Git `HEAD` used for this account before this documentation commit. The Python engine, web source, site-data generator and Kiro directory are committed. The generated `web/node_modules` directory is ignored.

## Hook record

The hook definitions are Kiro configuration. Their command actions can also be run directly.

On 19 August 2026, during this documentation pass, these actions were run from the repository root:

```text
python scripts/check_offline.py
Offline guard passed.

python scripts/check_redaction.py
Redaction gate passed.

python -m pytest tests -q -k "schema or adapter or golden"
19 passed, 92 deselected
```

No Kiro hook trigger was run during this documentation pass. The command actions behind `offline-guard`, `cassette-redaction-gate` and `adapter-golden-tests` were run manually and passed, but they were not captured as Kiro `PostFileSave` executions.

The `specification-drift-check` agent hook was not run during this documentation pass because it is a Kiro `PostTaskExec` action rather than a shell command. There is no committed hook execution log proving earlier Kiro-triggered runs. No hook caught a real violation. There is also no retained output showing the intentional guard failure requested by Task 1. The hooks therefore show enforceable configuration and current passing actions, not a history of defects caught.

## Verification record

The following commands were also run on 19 August 2026:

| Command | Observed result |
|---|---|
| `python -m pytest -q` | `111 passed` |
| `python -m ruff check .` | `All checks passed!` |
| `python -m mypy` | `Success: no issues found in 14 source files` |
| `python -m ferric.cli list --cassette-dir tests/cassettes` | Four validated cassettes: OpenAI, Anthropic and MCP evidence |
| `python -m ferric.cli verify --cassette-dir tests/cassettes` | Four cassettes passed schema, integrity hash and redaction checks |
| `FERRIC_MODE=replay python examples/demo-agent/agent.py` | Three deterministic local MCP tool calls, explicitly not Kiro production capture |
| `npm run lint` in `web` | Exit code 0 |
| `npm run typecheck` in `web` | Exit code 0 |
| `npm run build` in `web` | Redaction gate, cassette data generation, TypeScript build and Vite production build succeeded |

No provider key was used for these checks. No live drift command was run. No demo video or Kiro production session was captured. Browser automation, an external clean-machine run and release submission evidence remain outstanding.
