# Ferric, App Blueprint

## Product Summary

Ferric is a flight recorder for LLM and agent traffic. Wrap a model client in one line, it captures every prompt, tool call and response into a cassette on disk, then replays those cassettes in CI with no network access and no API spend. Assertions run on the shape of the interaction rather than the wording, so a test fails on a real behavioural regression and stays quiet when the model simply reworded itself.

Built for the Ready, Spec, Ship Hackathon sponsored by Kiro. Submissions close 23 August 2026 at 23:59 UTC. The core product remains a local developer tool. The deployed site adds a small Groq-backed demonstration route so a judge can record one interaction in the browser and replay it without another provider call.

Note on scope: this is a developer tool, not a SaaS product. There is no signup, database, payments or hosted cassette library. The deployed demonstration route is stateless and keeps its returned cassette in the browser session. The blueprint sections below that would normally cover pricing tiers, auth providers and infrastructure cost curves are answered honestly rather than invented, because a monetisation model fabricated for a hackathon submission is exactly the kind of thing the viability screen is looking for.

---

## The Problem

Every team shipping an AI feature has the same gap. The model call is the only part of the stack with no test coverage.

Three things make it hard. Output is non-deterministic, so string equality assertions break on rewording. Calling a live model in CI is slow, costs money on every run, and flakes on provider rate limits. And there is no shared vocabulary for what a correct agent interaction even looks like, so teams fall back to eyeballing behaviour in staging.

The failure mode is quiet. A prompt gets edited, an agent starts calling tools in a different order, and nothing catches it until a user reports something strange a fortnight later. The same thing happens on a model version upgrade, which teams currently perform as an act of faith.

---

## Who This Is For

**Backend and platform engineers who shipped an AI feature and now have to maintain it.** They already have a pytest suite for everything else. They are not evaluating models, they are trying to stop a working feature from silently breaking. This is the primary user and every design decision defers to them.

**Teams about to upgrade a model version.** They have no way to know what changes before they ship it. The drift report is aimed directly at this moment.

**Hackathon judges evaluating whether the submission genuinely runs.** A real audience with a real job, and the reason the demo fixture must work from a clean clone with no API key in under two minutes.

---

## Competitive Position

| Tool | What it does | What it does not do |
|---|---|---|
| VCR-style HTTP cassette libraries (vcrpy, betamax) | Record and replay raw HTTP at the transport layer | No understanding of tool calls, no semantic assertions, matching is on raw request bodies so any prompt edit breaks every cassette |
| promptfoo | Evaluation harness, runs prompts against models and scores outputs | Built for evaluation, not regression. Calls live models. No capture from production |
| LangSmith, Langfuse and similar observability platforms | Trace and inspect production LLM traffic | Observability, not testing. Traces are for reading, not for asserting against in CI. Hosted, so CI depends on a third-party service |
| Hand-rolled mocks | Whatever the team wrote | Diverge from reality immediately, and nobody updates them |

**The gap Ferric fills:** promotion from production, tool-call sequence assertions, and a model-upgrade drift report, in one offline package. No adjacent tool has all three. The wedge is that a cassette starts life as a real interaction that already happened, and the assertions are about interaction shape rather than text.

State this in the first fifteen seconds of the demo video. The crowded-adjacency risk is real and the answer to it is specificity, not volume.

---

## Feature Set

### Feature 1: Transparent capture

**User story:** as a developer, I want to record real model traffic without rewriting my call sites, so that adopting Ferric costs one line.

**Acceptance criteria:** a wrapped client forwards every request unmodified and returns the unmodified response. The request, response, model identifier, tool definitions in scope and wall-clock latency are persisted to a cassette. Provider errors are recorded as first-class events rather than discarded. With recording disabled, overhead is a single function call.

**Complexity:** medium. The work is in the adapters, not the wrapper.

### Feature 2: Hermetic replay

**User story:** as a developer, I want CI to run my AI tests offline, so that my suite is fast, free and deterministic.

**Acceptance criteria:** in replay mode the system serves responses from cassettes and never opens a socket to a provider. An unmatched request fails loudly with the request printed and the nearest cassette by fingerprint distance shown, and never falls through to the live provider. Replayed content is byte-identical to what was recorded, and repeated replays in one run return the same content.

**Complexity:** medium. The fingerprint design is the hard part, specifically deciding what to exclude.

### Feature 3: Promotion from production

**User story:** as a developer, I want to turn a real interaction that went wrong into a checked-in test, so that my regression suite is built from reality rather than imagination.

**Acceptance criteria:** `ferric promote <trace-id>` emits a runnable test file with default assertions. Secrets and personal data are redacted before the cassette is written to the repository. The generated test passes with no further editing.

**Complexity:** low, once the store and redactor exist.

### Feature 4: Behavioural assertions

**User story:** as a developer, I want assertions that survive non-determinism, so that my tests fail on real regressions and not on rewording.

**Acceptance criteria:** four families. Tool sequence compares observed against expected and reports the first divergence. Argument matching is exact on declared critical fields and ignores the rest. Schema validation reports the failing JSON path. Leakage fails if a declared pattern appears in any outbound request. Every failure prints the cassette identifier, expected and observed.

**Complexity:** medium. This is the differentiator and it deserves the time.

### Feature 5: Model drift reporting

**User story:** as a developer, I want to know what changes before I upgrade a model, so that upgrades stop being a leap of faith.

**Acceptance criteria:** `ferric drift --to <model>` replays the whole library against a target and classifies each cassette as unchanged, reworded, or behaviourally changed. Where behaviour changed, it names the dimension: tool selection, tool order, schema validity, or refusal. Total token spend is reported so the cost of the check is visible. `--html` writes a self-contained report that opens from the filesystem with no network.

**Complexity:** high, and it is the only feature requiring a live provider.

### The feature that carries the product

Feature 2. Everything else is useful, but offline hermetic replay is the thing that does not currently exist in a clean form, and it is the guarantee every other feature rests on.

---

## What Is Not Being Built

Named openly here, in the README, and on the landing page in Section 6 Cell F.

- Token-by-token streaming capture. Streaming responses are coalesced into a single assistant message
- Embeddings, image generation and audio endpoints
- A hosted service, a dashboard, or any account system
- Automatic assertion generation beyond the defaults `promote` writes
- Multi-turn conversation branching and replay of divergent paths
- Any provider beyond OpenAI, Anthropic and MCP tool calls

Each of these is a deliberate cut, not an oversight. A smaller honest tool beats a larger one that overstates itself, and the viability screen exists precisely to catch the second kind.

---

## Architecture

Ferric sits between application code and a model provider as a wrapping object, with two runtime modes selected by `FERRIC_MODE`, and a separate offline command surface.

```
app code
   |
   v
ferric.wrap(client)
   |
   +-- record mode --> provider --> event normaliser --> cassette store
   |
   +-- replay mode --> matcher --> cassette store  (no socket, ever)

CLI (separate from runtime, reads the store directly)
   promote · drift · list · verify
```

The core insight is that the unit of value is not the response text, it is the interaction shape. The cassette stores a normalised event log rather than a raw HTTP body, and every assertion operates on that log. This is what lets one assertion library work across three providers.

The CLI never touches application code, which means promotion and drift work on cassettes recorded by someone else.

---

## Data Structures

```python
class EventRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"

class Event(BaseModel):
    index: int                    # monotonic within the cassette
    role: EventRole
    payload: dict[str, Any]

class RedactionRecord(BaseModel):
    rule_class: str               # api_key, bearer_token, email, card, custom
    event_index: int
    field_path: str

class Cassette(BaseModel):
    id: str                       # content hash of the normalised event list
    provider: str                 # openai, anthropic, mcp
    model: str
    recorded_at: datetime
    fingerprint: str
    events: list[Event]
    redactions: list[RedactionRecord]

class ManifestEntry(BaseModel):
    id: str
    provider: str
    model: str
    recorded_at: datetime
    event_count: int

class DriftClassification(str, Enum):
    UNCHANGED = "unchanged"
    REWORDED = "reworded"
    DIVERGED = "diverged"

class DriftResult(BaseModel):
    cassette_id: str
    classification: DriftClassification
    dimension: str | None         # tool_selection, tool_order, schema, refusal
    baseline_events: list[Event]
    target_events: list[Event]
    tokens_spent: int
```

The redaction record is deliberately part of the cassette rather than a side log. A reviewer opening a cassette in a pull request needs to see that something was stripped and what class it was.

---

## CLI Surface

| Command | Purpose | Network |
|---|---|---|
| `ferric list` | Print the cassette library with provider, model and event count | no |
| `ferric verify` | Validate every cassette against the schema and the redaction rules | no |
| `ferric promote <trace-id>` | Generate a runnable test file from a recorded trace | no |
| `ferric drift --to <model>` | Replay the library against a target model, classify and report | yes |
| `ferric drift --to <model> --html <path>` | Additionally write the self-contained HTML report | yes |

Environment: `FERRIC_MODE` is `record`, `replay`, or unset for passthrough. That is the only required environment variable. A provider key is needed for `drift` only.

---

## Error Handling

An unmatched request in replay mode is a hard failure, with the full fingerprint printed alongside the nearest cassette by fingerprint distance. The most common cause is a prompt edit, and showing the neighbour turns a confusing error into an obvious one.

A provider error in record mode is recorded as an `ErrorEvent` and re-raised, so failure paths become testable rather than invisible.

A corrupt cassette fails the whole run rather than being skipped. Silently skipping a test is worse than failing it.

A redaction rule that matches on the write path strips the value and records the class. It never writes the raw value and warns, because a warning in CI output is a secret in CI output.

---

## Testing Strategy

The default suite is offline and that is enforced structurally, not by convention. `scripts/check_offline.py` runs as a Kiro hook on every test file save and fails if a network import appears outside the drift suite. The replay no-socket guarantee is tested by patching `socket.socket` and failing if it is called.

Adapters are tested with golden fixtures: a real captured payload with secrets stripped, normalised, and compared against a committed expected event list. The matcher is tested with deliberately perturbed fingerprints to prove it does not match loosely.

Ferric dogfoods itself. It records the MCP tool calls Kiro makes while building Ferric, and those cassettes ship as the demo fixture. This is both the strongest proof the tool works and the demo scene that lands.

---

## Monetisation

Ferric is open source under MIT and there is no monetisation for the hackathon. Stating a pricing table would be invented.

The honest post-hackathon path, if the project continues: the CLI and library stay free forever, because a testing tool that costs money at the point of running tests will not be adopted. The plausible commercial surface is a hosted drift service that runs the cassette library against new model versions on a schedule and reports before the team upgrades, which is the part that genuinely needs infrastructure. That is a post-competition question and it is not part of this submission.

---

## Distribution

Not part of the judged submission, listed because it shapes what gets built.

The tool ships on PyPI as `ferric`, installed with `pipx install ferric`. The repository is public on GitHub with the `.kiro` directory committed, which is a submission requirement and also the most interesting part of the repo for anyone evaluating spec-driven development.

Organic reach comes from the artefact rather than promotion: the drift report is a single HTML file people share, and every share carries `generated by ferric` in the footer. One post at submission, covered in MARKETING.md.

---

## Build Priority

Judging weights: Application Quality 40, Kiro Usage 20, Documentation 20, Innovation and Potential 15, Presentation 5. A pass-or-fail eligibility and viability screen runs before any of it.

1. The schema, store and redactor, because everything depends on the contract
2. Record and replay working end to end with the no-socket guarantee proven by test
3. The four assertion families
4. The demo fixture running from a clean clone with no key in under two minutes
5. The README and HOW-THIS-WAS-BUILT
6. The landing page, sections in order, cutting from the bottom if time runs short
7. The drift command and the HTML report
8. The demo video
9. Clean-machine test, then submit early on 23 August

Full day-by-day sequencing and the cut list are in BUILD_GUIDE.md.
