# Ferric, Build Guide

## Before You Write a Single Line of Code

Read CLAUDE.md, APP_BLUEPRINT.md and FRONTEND_SPEC.md in full. CLAUDE.md holds the design system and code rules. APP_BLUEPRINT.md holds the data structures, the CLI surface and the competitive position. FRONTEND_SPEC.md holds every class, animation value and z-index for all three web surfaces. This guide holds build order only.

Two constraints shape everything below.

**Nine days, not a month.** Submissions close 23 August 2026 at 23:59 UTC. The plan front-loads the contract and back-loads nothing. If a phase slips, the cut list at the bottom says exactly what gets dropped and in what order.

**Forty of the hundred points are not the app.** Kiro Usage is 20 and Documentation is 20. Phase 0 and Phase 6 are not overhead, they are a third of the score. Do not compress them to buy engine time.

---

## Prerequisites

```bash
python --version    # must be 3.11 or higher
node --version      # must be 18 or higher
npm --version       # must be 9 or higher
git --version
pipx --version      # install with: python -m pip install --user pipx
```

No API key is required to build or test Ferric. The default suite is fully offline. A provider key is needed only for Phase 5's drift command, which is excluded from the default test run by design.

Repository setup:

```bash
mkdir ferric && cd ferric
git init
python -m venv .venv && source .venv/bin/activate
pip install pydantic typer pytest pytest-cov ruff mypy
mkdir -p src/ferric/adapters tests/cassettes tests/goldens scripts examples/demo-agent
touch src/ferric/__init__.py src/ferric/adapters/__init__.py
```

Create `pyproject.toml` with the distribution name `ferric`, the package at `src/ferric`, and a console script entrypoint `ferric = "ferric.cli:app"`. Confirm `pip install -e .` works and `ferric --help` prints before writing any real code. A packaging problem discovered on day eight is fatal.

---

## Phase 0, Day 1, Specs Before Code

This phase produces no application code and it is not optional. It is worth 20 points on its own and it is the opening scene of the demo video.

### Step 0.1: Screen-record this entire session

Start recording before you open Kiro. Everything in this phase becomes the first sixty seconds of the demo video, showing specs being written before code exists. Save the raw capture, you will trim it on day eight.

### Step 0.2: Confirm the steering files

`.kiro/steering/product.md`, `tech.md` and `structure.md` are already written. Read them in Kiro and confirm they load. Correct anything that no longer matches, particularly any surviving reference to the old working title.

### Step 0.3: Confirm the specs

`.kiro/specs/ferric-core/requirements.md` holds six requirements written as acceptance criteria. `design.md` holds the architecture and the scope boundaries. `tasks.md` holds nineteen tasks mapped day by day, each referencing the criteria it satisfies. Open all three in Kiro and confirm the task list is parseable and drivable.

### Step 0.4: Confirm the hooks fire

Four hooks live in `.kiro/hooks/`. Two of them call scripts that do not exist yet, so write those first as minimal working versions:

`scripts/check_offline.py` reads the staged test files and fails with a non-zero exit if it finds an import of `requests`, `httpx`, `urllib`, `socket`, or a provider SDK outside the drift suite directory. Roughly thirty lines.

`scripts/check_redaction.py` reads any JSON file under `tests/cassettes/` and fails if it matches a secret pattern: `sk-`, `Bearer `, an email regex, or a sixteen-digit sequence. Roughly forty lines.

Then trigger each hook deliberately and watch it fire. A hook that has never run is not evidence of anything. Capture this in the recording.

### Step 0.5: First commit

Commit the specs, steering, hooks and scripts before any application code exists. The commit history is part of the Documentation score, and a first commit containing only specs is the cleanest possible proof of spec-driven development.

---

## Phase 1, Day 1 to 2, The Contract

Everything downstream depends on the event schema. Get it right before building anything on top of it.

### Step 1.1: The normalised event schema

`src/ferric/schema.py`. Pydantic models for the five event types: `UserMessage`, `AssistantMessage`, `ToolCall`, `ToolResult`, `ErrorEvent`. Each carries a role, a payload and a monotonic index. Then `Cassette` with an identifier, provider, model, recorded timestamp, request fingerprint, ordered event list and a redaction record. Then `Manifest`.

The redaction record matters. A reviewer needs to know something was removed and what class of thing it was.

Test: an invalid event is rejected at construction. A cassette with a non-monotonic index is rejected.

Satisfies requirements 1 and 2.

### Step 1.2: The cassette store

`src/ferric/store.py`. Write, read, list, content-hash identifier generation, and manifest consistency on every write.

The identifier is a hash of the normalised event list, not of the file bytes, so it is stable across formatting changes.

Test: round trip on disk, identifier stability across repeated writes, manifest stays consistent after a write and a delete.

Satisfies requirements 1 and 2.

### Step 1.3: The redactor

`src/ferric/redact.py`. Pattern rules for API keys, bearer tokens, emails and card numbers, plus user-declared rules from config. Runs on the write path, before anything reaches disk.

Test: a known secret injected into an event never appears in the written file, and the redaction record names the class that was stripped.

Satisfies requirement 3.

**Checkpoint:** three modules, full test coverage, no network, no provider dependency. If this is not done by end of day 2, cut the MCP adapter from Phase 2 immediately.

---

## Phase 2, Day 3 to 4, Capture and Replay

This is where the product starts existing.

### Step 2.1: The OpenAI adapter

`src/ferric/adapters/openai.py`. Translates request and response payloads into normalised events. Imports the OpenAI SDK lazily, inside the function, never at module import.

Test: golden test against a captured payload fixture in `tests/goldens/`. The fixture is a real recorded payload with secrets stripped, not a hand-written approximation.

### Step 2.2: The Anthropic adapter

`src/ferric/adapters/anthropic.py`. Same translation contract, same golden test shape.

### Step 2.3: The wrapper and record mode

`src/ferric/wrapper.py`. The one-line entry point:

```python
client = ferric.wrap(client)
```

Forwards every request unmodified, captures on the return path, records provider errors as `ErrorEvent` rather than discarding them, then re-raises.

Test: a wrapped client returns byte-identical output to an unwrapped one. Recording adds no behavioural change.

Satisfies requirement 1.

### Step 2.4: The matcher and replay mode

`src/ferric/matcher.py`. Builds the request fingerprint from the model identifier, the normalised message list and the tool definitions in scope, explicitly excluding timestamps and request identifiers.

On no match: raise, print the full fingerprint, and print the nearest cassette by fingerprint distance. The most common cause of an unmatched request is a prompt edit, and showing the nearest neighbour turns a confusing error into an obvious one.

Never fall through to the live provider. This is the single most important behaviour in the codebase.

Test: assert at the transport layer that no socket is opened in replay mode. Patch `socket.socket` and fail the test if it is called. Do not test this by observing that no cost was incurred, test it structurally.

Satisfies requirement 2.

**Checkpoint:** record a real interaction, replay it offline, get identical output. This is the minimum viable product. If day 4 ends without this working, cut the Anthropic adapter and ship OpenAI only.

---

## Phase 3, Day 5, Assertions

`src/ferric/assertions.py`. Four families, each reporting the divergence point rather than a boolean.

### Step 3.1: Sequence and arguments

`assert_tool_sequence` compares the observed sequence of tool names against the expected sequence and reports the first index where they diverge, with both sequences printed.

`assert_tool_arguments` does exact match on declared critical fields and ignores everything else. A reworded query string does not fail. A wrong account identifier does.

### Step 3.2: Schema and refusal

`assert_response_schema` validates against a JSON schema and reports the failing JSON path, for example `$.anomalies[2].confidence`, not just "validation failed".

`assert_refusal` checks that a refusal fired where one was expected.

### Step 3.3: Leakage

`assert_no_leakage` fails if a declared pattern appears in any outbound request across the cassette.

Every assertion failure prints the cassette identifier, the expected value and the observed value. Test each with a deliberately broken cassette.

Satisfies requirement 4.

---

## Phase 4, Day 5, The CLI

`src/ferric/cli.py`, built with typer. Four commands, kept deliberately small.

### Step 4.1: promote

`ferric promote <trace-id>` generates a runnable test file from a recorded trace with default assertions, redacted before writing.

Test: the generated file passes without any editing. This is the acceptance criterion, and a generated test that needs hand-fixing has failed.

Satisfies requirement 3.

### Step 4.2: drift

`ferric drift --to <model>` replays the library against a target model, classifies each cassette as unchanged, reworded or behaviourally changed, names the dimension that moved, and reports total token spend.

This is the one part of Ferric that requires an API key and network access. Keep it entirely outside the default test suite.

`ferric drift --html report.html` additionally writes the self-contained report described in FRONTEND_SPEC.md Surface 2.

Satisfies requirement 5.

### Step 4.3: list and verify

`ferric list` prints the cassette library with model, provider and event count. `ferric verify` checks every cassette against the schema and the redaction rules, and is the command a judge runs to confirm the library is sound.

---

## Phase 5, Day 6, The Report Generator and the Demo Fixture

### Step 5.1: The report generator

`src/ferric/report.py`. Generates the single self-contained HTML file specified in FRONTEND_SPEC.md Surface 2. Inlined CSS in a `<style>` block, vanilla JS in a `<script>` block, system font stack, zero external requests.

Build it as a Python string template with the results injected as a JSON blob the inline script reads. Do not reach for jinja2, this is one template and forty lines of string formatting.

Verify by opening the output file directly from the filesystem with the network disabled. If anything fails to render, it has an external dependency that must be removed.

### Step 5.2: The demo fixture

`examples/demo-agent/`. A small agent with three tools that a judge can run in under two minutes:

```bash
git clone <repo> && cd ferric
pip install -e .
FERRIC_MODE=replay pytest
```

Committed cassettes, no API key, no network. The suite passes.

### Step 5.3: Dogfood Kiro

Record the MCP tool calls Kiro makes while building Ferric, using the MCP adapter. Commit those cassettes into `examples/demo-agent/cassettes/`. This is the demo video's strongest scene and it is the Kiro Usage evidence in artefact form. If the MCP adapter is not working by day 6, this is the first thing to cut, and Kiro Usage then rests on the specs and hooks alone, which is still a strong position.

### Step 5.4: The site data generator

`scripts/build_site_data.py` reads `tests/cassettes/`, extracts the values the landing page displays, and writes `web/src/data/cassettes.generated.ts`. Wire it into the web build as a prebuild step.

This is the mechanism behind Authenticity Rule 1. After this runs, no component contains a hand-typed cassette value, and the page cannot diverge from the artefacts.

---

## Phase 6, Day 6 to 7, The Web Surfaces

Read the matching section of FRONTEND_SPEC.md before writing each component. This guide gives order and setup, the spec gives every class and animation value.

### Step 6.1: Scaffold

```bash
cd web
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install motion gsap
mkdir -p src/components/{ui,layout,sections} src/hooks src/styles src/data
```

### Step 6.2: Tailwind config and global CSS

Map every CSS variable from FRONTEND_SPEC.md's Global Rules into `tailwind.config.ts` under `theme.extend`, and the font families under `fontFamily` as `display`, `body` and `mono`.

`src/styles/globals.css` carries the variable block, the semantic z-index scale, the `.tech-grid` and `.scanlines` utilities, the `recordPulse` and `shimmer` keyframes, the scrollbar hiding rules and the reduced-motion overrides. Take all values verbatim from the spec, do not redefine anything.

### Step 6.3: index.html

Single font link, the inline SVG data URI favicon, and the tab title `Ferric`. No favicon file, no logo, no manifest icons.

### Step 6.4: Utility components

`Icon.tsx` with six hand-written inline SVG paths: record dot, play, arrow-right, arrow-up-right, copy, check. Stroke width 1.5, `currentColor`, 24x24 viewBox, selected by a `name` prop.

`GrainOverlay.tsx`, `Skeleton.tsx`, `BlurText.tsx` for the word-by-word hero reveal, and `CopyButton.tsx` with the check-swap state and an `aria-live` announcement.

### Step 6.5: Hooks

`useSessionTimecode.ts` drives the nav timecode through one `requestAnimationFrame` loop writing to a ref, never to state. `useReducedMotion.ts` combines the media query with an `lg` breakpoint check and is consumed by the Recorder section before GSAP is registered. `useMagneticHover.ts` uses `useMotionValue` and `useTransform` with a 5px maximum drift.

### Step 6.6: Sections, in build order

Build in page order so the layout can be checked as it accumulates:

1. `Nav.tsx`, dual-pill with the session timecode and the mobile overlay
2. `Hero.tsx`, headline top-left, recorder readout bottom-right, technical grid, magnetic primary CTA
3. `Untested.tsx`, full-width statement with the scroll-driven weight shift behind an `@supports` guard
4. `Recorder.tsx`, the GSAP pinned three-phase sequence. Budget most of a day for this one section. Check the reduced-motion and mobile fallbacks before considering it done
5. `Assertions.tsx`, the tabbed explorer with the `layoutId` underline
6. `Anatomy.tsx`, the bento grid and the hand-authored Blueprint SVG schematic with the animated leader lines
7. `Install.tsx`, the command block and copy button
8. `Footer.tsx`

Every section imports its data from `src/data/cassettes.generated.ts`. No hand-typed values.

### Step 6.7: The docs site

Same Vite app, route at `/docs`. Three-column layout, the sidebar groups from FRONTEND_SPEC.md Surface 3, the on-page table of contents driven by an IntersectionObserver on every h2 and h3. Almost no motion, deliberately.

Eighteen pages across six groups. Write them from the specs and the code, not from imagination. If a page would document something not built, write the limitation instead.

### Step 6.8: Config

`src/config.ts` holds the repository URL and the demo video URL. Until the video exists, the two CTAs pointing at it render `aria-disabled="true"` with `pointer-events-none` and `opacity-50`. A dead link that looks live is worse than one that visibly is not ready.

---

## Phase 7, Day 7, Documentation

Documentation carries 20 points and most entrants will treat it as an afterthought. This is the cheapest scoring opportunity in the competition.

### Step 7.1: README.md

Structure, in this order:

1. One sentence on what Ferric does
2. The problem, in three sentences, concrete
3. Install and a sixty-second quickstart a judge can paste
4. How replay works, with the no-network guarantee stated explicitly
5. The four assertion families with a code example each
6. The drift command and a link to a committed sample report
7. Stated limitations, verbatim from Section 6 Cell F
8. How this was built with Kiro, linking to the deep-dive document
9. Testing instructions, exactly what a judge should run and what they should see

No badges beyond build status. No feature claimed that is not implemented.

### Step 7.2: docs/HOW-THIS-WAS-BUILT.md

The spec-to-tasks-to-hooks-to-code trail with real commit links. Show the requirement, show the task that referenced it, show the commit that closed it, show the hook that guards it. Include the moment a hook caught something, if it did, and say so plainly if it did not.

This single file targets both Kiro Usage and Documentation, forty points between them, and almost no competitor will write it deliberately.

### Step 7.3: Docstrings and inline documentation

Every module, class and public function. `ruff` and `mypy` clean.

---

## Phase 8, Day 8, The Demo Video

Three minutes maximum. No intro music, no slides, no talking head.

| Time | Content |
|---|---|
| 0:00 to 0:20 | The problem. A real AI feature, a prompt edit, nothing catches it |
| 0:20 to 1:20 | Live: record a real interaction, replay it offline, then change the model version and watch the tool-order assertion fail |
| 1:20 to 2:20 | The Kiro trail. The day-one spec session from Phase 0, the tasks driving the build, a hook firing, and the cassettes of Kiro's own tool calls |
| 2:20 to 2:45 | Install and the offline test suite passing on a clean machine |
| 2:45 to 3:00 | The drift report open in a browser, and the limitations named out loud |

Record at 1080p minimum. Upload to YouTube, unlisted is acceptable. Put the link in `src/config.ts`, remove the disabled state from both CTAs, and redeploy.

---

## Phase 9, Day 9, Submit

### Step 9.1: Clean-machine test

On a machine or container that has never seen this project:

```bash
git clone <public repo url> && cd ferric
pip install -e .
FERRIC_MODE=replay pytest
ferric verify
```

Everything must pass with no API key and no manual steps. If it does not, fix it before anything else.

### Step 9.2: Final audit

- `.kiro/` directory is committed and present in the public repository
- README matches what the code actually does, claim by claim
- Demo video link is live and publicly viewable
- No `viewport={{ once: true }}` anywhere: `grep -rn "once: true" web/src`
- No green in the palette: `grep -rn "22c55e\|4ade80\|34d399\|green-" web/src`
- No hardcoded hex in components: `grep -rn "#[0-9a-fA-F]\{6\}" web/src/components`
- No stale references to the old working title: `grep -rni "rewind" . --exclude-dir=.git`
- No em dashes in any file
- GSAP ScrollTrigger instances killed on unmount, confirmed by navigating away mid-scroll with the console open
- Reduced motion confirmed by toggling the OS setting and reloading
- Mobile viewport, all eight sections readable, no horizontal overflow
- Drift report opens from the filesystem with the network disabled
- Every number on the landing page traces to a file in `tests/cassettes/`

### Step 9.3: Submit

Submit through the official Google Form: repository link, demo video link, and the required project details. Submit early in the day. Do not submit in the final hour, a failed upload at 23:50 UTC ends the run.

---

## Cut List

If the schedule slips, cut in this exact order. Each cut is a whole feature removed cleanly and named as a limitation, never a feature left half-wired.

1. The MCP adapter and the Kiro dogfooding cassettes. Kiro Usage then rests on specs and hooks, still strong
2. The docs site. The README covers most of the same ground and carries the same points
3. The Anthropic adapter. Ship OpenAI only, name it in limitations
4. The `promote` command. The assertion library still stands alone
5. The Anatomy section's animated leader lines. Render the schematic static
6. The scroll-driven weight shift in Section 3. It is behind an `@supports` guard already

Never cut: the offline replay guarantee, the pinned Recorder section, the README, the demo video, or the clean-machine test. Those five are the submission.
