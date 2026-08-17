# Ferric Core Requirements

## Requirement 1: Transparent Capture

**User story:** As a developer maintaining an AI feature, I want to record real interactions through my existing client, so that adoption does not alter application behaviour.

### Acceptance Criteria

1.1 WHEN an application wraps a supported client and sends a request in record mode, THE SYSTEM SHALL forward the request without changing its model, messages, tools or arguments.

1.2 WHEN the provider returns successfully, THE SYSTEM SHALL return byte-identical response content and persist the provider, model, tool definitions, wall-clock latency and ordered normalised events.

1.3 IF the provider raises an error, THEN THE SYSTEM SHALL persist an error event and re-raise the original failure.

1.4 WHEN recording is disabled, THE SYSTEM SHALL pass calls through with no file write and no provider SDK imported at package import time.

1.5 WHEN events are stored, THE SYSTEM SHALL assign monotonic indexes and a content-hash identifier that remains stable across JSON formatting changes.

## Requirement 2: Hermetic Replay

**User story:** As a developer running CI, I want recorded interactions to replay without a provider, so that tests are deterministic, fast and free.

### Acceptance Criteria

2.1 WHEN replay mode receives a request with an exact cassette fingerprint, THE SYSTEM SHALL return the recorded content byte for byte and repeat the same result within the run.

2.2 WHILE replay mode is active, THE SYSTEM SHALL NOT open a network socket, instantiate a provider transport or require a provider key.

2.3 IF no exact fingerprint exists, THEN THE SYSTEM SHALL fail without calling a provider and report the request fingerprint plus the nearest cassette by fingerprint distance.

2.4 WHEN a fingerprint is built, THE SYSTEM SHALL include the model, normalised messages and tools in scope, and exclude timestamps and request identifiers.

2.5 IF a cassette is corrupt or invalid, THEN THE SYSTEM SHALL fail the run rather than skip the cassette.

## Requirement 3: Safe Promotion And Redaction

**User story:** As a developer investigating a real failure, I want to promote its trace into a safe test, so that the regression fixture reflects production without exposing private data.

### Acceptance Criteria

3.1 WHEN a cassette is written or promoted, THE SYSTEM SHALL redact API keys, bearer tokens, email addresses, 16 digit card patterns and configured custom patterns before any raw value reaches disk.

3.2 WHEN redaction occurs, THE SYSTEM SHALL record the rule class, event index and field path without retaining or printing the matched value.

3.3 WHEN `ferric promote <trace-id>` succeeds, THE SYSTEM SHALL write a runnable pytest file with default behavioural assertions that passes without manual editing.

3.4 IF a trace identifier is absent or invalid, THEN THE SYSTEM SHALL fail with an actionable message and SHALL NOT create a partial cassette or test file.

3.5 WHEN `ferric verify` inspects the library, THE SYSTEM SHALL reject schema-invalid or unredacted cassette JSON and identify the file and safe location of each failure.

## Requirement 4: Behavioural Assertions

**User story:** As a developer testing non-deterministic output, I want assertions on interaction shape, so that wording changes stay quiet and behavioural regressions fail.

### Acceptance Criteria

4.1 WHEN tool sequence is asserted, THE SYSTEM SHALL compare ordered tool names and report the first divergent index with expected and observed sequences.

4.2 WHEN critical arguments are asserted, THE SYSTEM SHALL compare only declared fields exactly and ignore undeclared fields.

4.3 WHEN a response schema is asserted, THE SYSTEM SHALL validate structured output and report the failing JSON path.

4.4 WHEN leakage is asserted, THE SYSTEM SHALL inspect every outbound request for declared patterns and report the event and field path without printing the matched value.

4.5 IF any behavioural assertion fails, THEN THE SYSTEM SHALL include the cassette identifier, expected value and observed value, except where redaction safety requires a class name instead of the raw value.

## Requirement 5: Model Drift Reporting

**User story:** As a team preparing a model upgrade, I want to compare the cassette library against a target model, so that changed behaviour is visible before release.

### Acceptance Criteria

5.1 WHEN `ferric drift --to <model>` runs, THE SYSTEM SHALL evaluate every valid cassette and classify it as unchanged, reworded or diverged.

5.2 IF a cassette diverges, THEN THE SYSTEM SHALL name tool selection, tool order, schema validity or refusal as the changed dimension.

5.3 WHEN a drift run completes, THE SYSTEM SHALL report total token spend and per-classification totals.

5.4 WHEN `--html <path>` is supplied, THE SYSTEM SHALL write one HTML file with inlined CSS and vanilla JavaScript that renders and filters from the filesystem without a network request.

5.5 WHILE the default test suite runs, THE SYSTEM SHALL exclude live drift tests, network imports and provider SDK imports outside `tests/drift/`.

## Requirement 6: Verifiable Delivery

**User story:** As a judge or new contributor, I want a truthful, documented demonstration, so that I can verify Ferric without private infrastructure or invented evidence.

### Acceptance Criteria

6.1 WHEN a clean environment installs the project and runs `FERRIC_MODE=replay pytest`, THE SYSTEM SHALL pass the default suite without an API key or network access in under two minutes.

6.2 WHEN the demo agent runs in replay mode, THE SYSTEM SHALL use committed redacted cassettes, exercise three tools and make no provider call.

6.3 WHEN the landing page displays cassette content or metrics, THE SYSTEM SHALL derive them from `tests/cassettes/` at build time or display a skeleton state if evidence is absent.

6.4 THE SYSTEM SHALL provide the eight landing sections, the responsive docs route and the responsive self-contained report specified in `FRONTEND_SPEC.md`, including reduced-motion and disabled-link states.

6.5 THE SYSTEM SHALL state the exclusions for token streaming, embeddings, image and audio endpoints, hosted services, branching and unsupported providers in public documentation.

6.6 WHEN project invariants change, THE SYSTEM SHALL use Kiro hooks to run offline, golden, redaction and specification-drift checks at the relevant edit or task boundary.
