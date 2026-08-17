# Ferric Core Implementation Tasks

Tasks are ordered by dependency and build day. A task is complete only when its named tests pass and its mapped acceptance criteria have evidence.

- [ ] 1. Establish the package and offline test boundary, Day 1
  - Create the Python 3.11 package, Typer entry point, development commands and pytest configuration that excludes `tests/drift/` by default.
  - Run the offline and redaction hook scripts from a clean checkout state.
  - Evidence: editable installation, `ferric --help`, guard script pass and an intentional guard failure.
  - Criteria: 1.4, 2.2, 5.5, 6.6

- [ ] 2. Implement the validated event and cassette schema, Day 1
  - Add event roles, ordered events, redaction records, cassettes, manifests and drift result models.
  - Reject invalid payloads, non-monotonic indexes and inconsistent identifiers.
  - Evidence: focused schema unit tests.
  - Criteria: 1.2, 1.5, 2.5, 3.2

- [ ] 3. Implement the cassette store, Day 2
  - Add atomic write, read, list and delete operations with stable canonical content hashes and manifest consistency.
  - Evidence: disk round-trip, formatting stability and manifest update tests.
  - Criteria: 1.5, 2.1, 2.5

- [ ] 4. Implement write-path redaction, Day 2
  - Add built-in rules for API keys, bearer tokens, email addresses and 16 digit card patterns plus configured custom rules.
  - Traverse nested event values, replace before serialisation and record safe rule metadata.
  - Evidence: injected-secret tests prove raw values never reach a file or failure message.
  - Criteria: 3.1, 3.2, 3.5, 4.4

- [ ] 5. Implement the OpenAI adapter and golden, Day 3
  - Normalise a stripped real request, response, tool call and provider error fixture.
  - Import the SDK only inside the adapter call path.
  - Evidence: committed golden comparison and package-import isolation test.
  - Criteria: 1.1, 1.2, 1.3, 1.4

- [ ] 6. Implement the Anthropic adapter and golden, Day 3
  - Match the shared normalisation contract using stripped real Anthropic fixtures.
  - Evidence: adapter golden and error normalisation tests.
  - Criteria: 1.1, 1.2, 1.3, 1.4

- [ ] 7. Implement the MCP adapter and Kiro fixture capture, Day 3
  - Normalise MCP tool requests and results without coupling the core schema to Kiro.
  - Prepare a redacted cassette shape for the demo fixture.
  - Evidence: MCP golden and redaction check.
  - Criteria: 1.2, 3.1, 6.2

- [ ] 8. Implement wrapping, passthrough and record mode, Day 4
  - Add `ferric.wrap(client)`, mode selection, unmodified forwarding, response preservation and error recording with re-raise.
  - Evidence: spy-client tests compare wrapped and unwrapped arguments and bytes, plus provider error tests.
  - Criteria: 1.1, 1.2, 1.3, 1.4

- [ ] 9. Implement fingerprints, matching and replay mode, Day 4
  - Canonicalise stable request fields, perform exact lookup, return stable recorded content and report nearest cassette on a miss.
  - Remove every provider fallback from the replay branch.
  - Evidence: exact match, perturbed fingerprint, repeated replay, patched socket and fail-on-provider-call tests.
  - Criteria: 2.1, 2.2, 2.3, 2.4, 2.5

- [ ] 10. Implement behavioural assertions, Day 5
  - Add tool sequence, critical argument, JSON schema and leakage assertions with safe divergence diagnostics.
  - Add refusal comparison for drift classification support.
  - Evidence: one passing and deliberately broken cassette per assertion family.
  - Criteria: 4.1, 4.2, 4.3, 4.4, 4.5

- [ ] 11. Implement list, verify and promote commands, Day 5
  - Keep Typer handlers thin and delegate schema, store, redaction and assertion work.
  - Make promotion atomic and generate a pytest file that runs without editing.
  - Evidence: CLI runner tests, invalid trace test and execution of the generated test.
  - Criteria: 3.1, 3.3, 3.4, 3.5

- [ ] 12. Implement drift comparison and accounting, Day 5
  - Compare the library against normalised target events, classify unchanged, reworded and diverged results, and identify changed dimensions.
  - Keep live provider cases under `tests/drift/` only.
  - Evidence: offline classification matrix and token total tests.
  - Criteria: 5.1, 5.2, 5.3, 5.5

- [ ] 13. Implement the self-contained drift report, Day 6
  - Generate escaped inline result data, CSS and vanilla JavaScript with filters, single-row expansion, responsive layout and print rules.
  - Evidence: file opens from the filesystem, contains no external resource URL and works at desktop and mobile widths.
  - Criteria: 5.4, 6.4

- [ ] 14. Build the replay demo fixture, Day 6
  - Add a three-tool demo agent, committed redacted cassettes and a test command that needs no key.
  - Record Kiro MCP traffic when the adapter is available and keep the fixture truthful if it is cut.
  - Evidence: demo test under a socket block and redaction verification.
  - Criteria: 2.2, 3.1, 6.1, 6.2

- [ ] 15. Build cassette-derived site data and web foundations, Day 6
  - Add the Vite React application, Tailwind tokens, fonts, inline favicon, semantic layers, reduced-motion rules and shared utilities.
  - Generate TypeScript display data from validated cassettes during prebuild, with skeleton fallbacks.
  - Evidence: production build, generated-data test and scans for banned values and patterns.
  - Criteria: 6.3, 6.4

- [ ] 16. Build the nav, hero and untested layer, Day 6
  - Implement the session timecode without React state, responsive dual-pill navigation, cassette-derived readout and reduced-motion-safe entrances.
  - Evidence: component tests plus desktop and mobile visual checks with no overflow.
  - Criteria: 6.3, 6.4

- [ ] 17. Build the recorder, assertions, anatomy, install and footer, Day 7
  - Implement the sole GSAP pinned sequence and its stacked fallback, live assertion tabs, cassette schematic, limitations cell, install controls and truthful link states.
  - Use only generated cassette evidence in all result panels.
  - Evidence: interaction tests, ScrollTrigger cleanup test, reduced-motion check and responsive visual checks.
  - Criteria: 4.1, 4.2, 4.3, 4.4, 6.3, 6.4, 6.5

- [ ] 18. Build the docs route and project documentation, Day 7
  - Add the responsive three-column docs surface, search trigger, copy controls, active heading tracking and all documented pages.
  - Write README and build-history documentation from implemented behaviour, including setup, verification, Kiro evidence and limitations.
  - Evidence: link and accessibility checks, docs build and claim-by-claim implementation review.
  - Criteria: 6.4, 6.5, 6.6

- [ ] 19. Run release verification and prepare the submission, Days 8 to 9
  - Run formatting, lint, typing, offline tests, cassette verification, hook scripts, web build, filesystem report check and clean-machine replay.
  - Audit stale names, em dashes, green, hardcoded component hex, one-time viewport animation, external report resources and hand-typed cassette values.
  - Record the three-minute demonstration, set the real video URL, repeat disabled-link and clean-clone checks, and submit early.
  - Evidence: captured command output, clean-machine result and final acceptance matrix for all criteria.
  - Criteria: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
