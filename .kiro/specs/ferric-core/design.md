# Ferric Core Design

## Overview

Ferric wraps an existing model client and presents three execution paths. Passthrough preserves the original call. Record invokes the provider and writes a redacted normalised cassette. Replay resolves the request against local cassettes and has no provider path. A separate CLI reads the same store for promotion, verification, listing and drift analysis.

```text
application
    |
    v
ferric.wrap(client)
    |
    +-- passthrough -----------------------> provider
    |
    +-- record -> provider -> adapter -> redactor -> cassette store
    |
    +-- replay -> fingerprint -> matcher -> cassette store

CLI -> list | verify | promote | drift -> report
```

## Goals

- Preserve wrapped client behaviour in record and passthrough modes.
- Make replay structurally offline and deterministic.
- Store provider-neutral interaction shape in reviewable JSON.
- Remove sensitive values before serialisation.
- Report behavioural divergence at a useful location.
- Produce a clean-clone demo and truthful static web surfaces.

## Non-Goals

The competition build does not provide token-level streaming capture, embeddings, image or audio endpoints, a hosted service, accounts, payments, branching replay, automatic assertion design beyond promotion defaults, or adapters beyond OpenAI, Anthropic and MCP.

## Domain Model

`EventRole` contains `user`, `assistant`, `tool_call`, `tool_result` and `error`. Each `Event` has a monotonic `index`, a role and a provider-neutral payload. Provider-specific fields remain inside an adapter unless they are required for faithful response replay.

`Cassette` contains its content-hash identifier, provider, model, UTC recording time, request fingerprint, ordered events and redaction records. A `RedactionRecord` contains a rule class, event index and field path. A manifest entry contains only list metadata and is updated atomically with store changes.

`DriftResult` contains the cassette identifier, classification, optional changed dimension, baseline events, target events and token spend.

Pydantic validates each external payload and each file read. Cassette validation checks monotonic event indexes and identifier consistency.

## Fingerprinting And Matching

The canonical fingerprint input contains the model identifier, normalised message list and canonical tool definitions. Dictionary keys are sorted and JSON uses stable separators before hashing. Provider request identifiers, timestamps, latency and unrelated transport metadata are excluded.

Replay accepts exact fingerprint equality only. Fingerprint distance is diagnostic and never authorises a loose match. On a miss, the matcher raises an unmatched-request error containing the new fingerprint and the nearest cassette identifier. The wrapper does not retain a callable provider fallback in the replay branch.

## Capture Flow

1. `wrap` reads `FERRIC_MODE` and chooses one path.
2. Record mode forwards the original call arguments to the original client.
3. The adapter converts the request and response into ordered events.
4. The redactor walks all payload values before serialisation.
5. The store calculates the identifier from canonical normalised events and updates the cassette and manifest.
6. The wrapper returns the original response content.

If the provider raises, the adapter records a safe error event, the store writes the failure cassette, and the wrapper re-raises the original exception. Provider SDK imports occur inside adapter entry points.

## Replay Flow

1. The wrapper canonicalises the incoming request without importing a provider SDK.
2. The matcher performs exact lookup in the validated store.
3. A match reconstructs the recorded response in the shape expected by the wrapped client.
4. A miss raises before any provider object or socket can be created.

Tests patch `socket.socket` to fail on use and provide a client whose provider method also fails if called. Repeated calls prove stable output.

## Redaction And Promotion

Built-in redaction classes cover API keys, bearer tokens, email addresses and 16 digit card patterns. User rules extend the same interface. Redaction traverses nested mappings and sequences, replaces the value in memory and records its event and field path. Messages, exceptions and hook output identify only the rule class and location.

`promote` loads a validated recorded trace, applies redaction again as a boundary defence, writes it to the test cassette library, and generates a pytest file with default sequence, critical argument, schema and leakage assertions when evidence for each family exists. File writes use temporary files and replacement so a failed promotion leaves no partial output.

## Assertions

Assertion functions accept validated events and raise focused assertion errors. Sequence comparison reports the first differing tool index. Argument comparison resolves declared field paths and ignores all other values. Schema validation reports a JSON path. Leakage walks outbound request fields and reports a safe location. All failures include the cassette identifier and expected and observed values where those values are not sensitive.

## Drift

Drift is the only live-provider workflow. It reads every valid cassette, invokes the selected target adapter, normalises the target events and compares interaction shape before text. Equal events are unchanged. Equal behaviour with changed assistant prose is reworded. Changes to tool selection, tool order, schema validity or refusal are diverged and carry that dimension.

Live drift tests live under `tests/drift/` and are not part of the default pytest target. Unit tests use fixed normalised target events.

The report generator injects escaped result JSON into a single HTML template. CSS and JavaScript are inline. Filtering and one-row expansion use vanilla JavaScript. No font, image, script or stylesheet URL is emitted. Print and mobile rules follow `FRONTEND_SPEC.md`.

## CLI

| Command | Behaviour | Network |
|---|---|---|
| `ferric list` | List identifier, provider, model and event count | no |
| `ferric verify` | Validate schema, identifiers and redaction | no |
| `ferric promote <trace-id>` | Create a redacted cassette and runnable test | no |
| `ferric drift --to <model>` | Compare all cassettes with a target model | yes |
| `ferric drift --to <model> --html <path>` | Also write the offline report | yes |

Typer command handlers remain thin. Domain failures map to concise messages and non-zero exit codes.

## Web Surfaces

The Vite application owns the landing page and docs route. The landing page uses eight ordered sections: dual-pill nav, hero, untested layer, recorder, assertions, cassette anatomy, install and footer. The recorder is the only GSAP owner. Other landing animation uses `motion/react` and replays on re-entry. Mobile and reduced-motion modes replace the pin with a stacked recorder.

`scripts/build_site_data.py` validates `tests/cassettes/` and generates TypeScript data before the web build. Components render generated evidence or skeletons. They do not copy cassette content. The docs route uses the same visual tokens with restrained motion. Video links remain visibly disabled until a real URL exists.

## Error Handling

- Invalid events and cassettes fail at their boundary.
- Corrupt cassettes fail the run and are not skipped.
- Replay misses fail with fingerprint diagnostics and no fallback.
- Record errors are captured safely and re-raised.
- Redaction failures stop the write.
- Drift provider failures identify the cassette and stop or mark the run according to the command policy, without fabricating a classification.
- Report generation escapes embedded data and writes atomically.

## Security And Privacy

The store write path always passes through redaction. Verification repeats scanning for defence in depth. Hook output never includes matched data. The default suite cannot import known network modules or provider SDKs outside `tests/drift/`. The report contains only validated, redacted cassette data and makes no external requests.

## Verification Strategy

- Schema construction tests cover invalid roles, payloads and event order.
- Store tests cover round trips, stable hashes and manifest consistency.
- Redaction tests inject every built-in pattern into nested cassette fields.
- Adapter golden tests compare stripped real payloads with expected event lists.
- Wrapper tests prove argument and response identity plus error capture.
- Replay tests patch the socket and provider call, cover exact hits, misses and corrupt files.
- Assertion tests use deliberately broken cassettes and inspect divergence detail.
- CLI tests execute generated promotion files and inspect exit codes.
- Drift tests cover all classifications and report rendering without external resources.
- Web tests cover generated data, responsive overflow, accessibility, reduced motion and disabled links.
- A clean-machine run proves installation, replay, verification and the two guard scripts.

## Requirement Trace

| Requirement | Primary components |
|---|---|
| 1 | schema, store, adapters, wrapper |
| 2 | matcher, store, wrapper |
| 3 | redact, store, CLI, verification hook |
| 4 | assertions |
| 5 | drift command, adapters, report |
| 6 | demo fixture, data generator, web, docs, Kiro hooks |
