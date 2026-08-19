# Ferric, Agent Context

## What This Is

Ferric is a flight recorder for LLM and agent traffic. You wrap an existing model client in one line, it captures every prompt, tool call and response into a signed cassette on disk, then replays those cassettes in CI with no network access and no API spend. Assertions run on the shape of the interaction rather than the wording, so tests survive non-determinism.

Built for the Ready, Spec, Ship Hackathon sponsored by Kiro, presented by John Crickett, Angie Jones and Gregor Ojstersek. Submissions close 23 August 2026 at 23:59 UTC. Judging runs 24 August to 5 September, winners announced 6 September.

The problem it solves: teams are shipping AI features they cannot regression test. Output is non-deterministic so string equality is useless, and calling a live model in CI is slow, costly and flaky. The current state of the art is eyeballing behaviour in staging. Ferric replaces that with deterministic offline replay and property-based assertions.

## Name

Ferric, one word. It is iron oxide, the magnetic coating on recording tape, the material that made recording and playback possible. Verified unclaimed on PyPI on 15 August 2026. It is the distribution name, the import name, the CLI entrypoint and the source directory, with no hyphen and no suffix.

`rewind` was the working title through the spec phase and is already taken on PyPI by an existing AGPL project. Every reference in this repository uses `ferric`. If you find `rewind` anywhere, it is a stale artefact and should be corrected.

## One-Line Pitch

Your AI feature has no test suite. Ferric is the one it should have had.

## MVP Features

1. **Transparent capture.** Wrap a supported client in one line. Every request is forwarded untouched, every response returned untouched, and the normalised event log is captured on the way back. Errors are recorded as first-class events, not discarded.
2. **Hermetic replay.** In replay mode the runtime serves responses from cassettes and never opens a socket to a provider. An unmatched request fails loudly with the nearest cassette printed by fingerprint distance, it never falls through to the live model.
3. **Promotion from production.** `ferric promote <trace-id>` turns a real recorded interaction into a runnable test file with default assertions, redacted before it reaches the repository.
4. **Behavioural assertions.** Four families: tool call sequence, critical argument matching, JSON schema validity, and redaction leakage. Each reports the divergence point, not a bare boolean.
5. **Model drift reporting.** `ferric drift --to <model>` replays the whole cassette library against a target model and classifies every cassette as unchanged, reworded, or behaviourally changed, naming the dimension that moved. Outputs a self-contained HTML report.

Out of scope for the competition period, stated openly on the marketing page and in the docs: token-by-token streaming capture, embeddings, image and audio endpoints.

## Stack

| Layer | Technology |
|---|---|
| Engine | Python 3.11+, pydantic for the event schema, typer for the CLI |
| Testing | pytest, offline cassette suite as the default target |
| Cassette format | Plain JSON on disk, content-hashed identifiers, readable in a pull request |
| Landing page | React 18 + Vite + TypeScript |
| Styling | Tailwind CSS |
| Animation | motion/react, plus GSAP ScrollTrigger in the Recorder section only |
| Report viewer | Single self-contained HTML file, inlined CSS and vanilla JS, zero dependencies |
| Docs site | Same Vite app, separate route, MDX or plain TSX pages |
| Deployment | Vercel or Netlify, static build, no serverless function needed |

No database. No auth. No payments. The Python engine remains local-first and runs in developer machines and CI. The deployed web surface also includes a deliberately small server-side Groq demonstration route. It keeps the provider key server-side and returns a browser-session cassette for local replay. It is not a hosted cassette store or account service.

## Project Structure

```
ferric/
├── src/ferric/
│   ├── schema.py           normalised events, cassette and manifest types
│   ├── store.py            cassette read, write, list, hashing, manifest
│   ├── redact.py           redaction rules and the write path filter
│   ├── wrapper.py          the one line entry point, record and replay switch
│   ├── matcher.py          request fingerprint and cassette lookup
│   ├── assertions.py       sequence, arguments, schema, leakage
│   ├── report.py           the self-contained HTML drift report generator
│   ├── cli.py              promote, drift, list, verify
│   └── adapters/
│       ├── openai.py
│       ├── anthropic.py
│       └── mcp.py
├── tests/
│   ├── cassettes/          committed golden cassettes, post-redaction
│   ├── goldens/            expected normalised event lists per adapter
│   └── test_*.py
├── examples/demo-agent/    the runnable demo a judge clones
├── scripts/
│   ├── check_offline.py    hook target, blocks network calls in the default suite
│   ├── check_redaction.py  hook target, blocks unredacted cassettes
│   └── build_site_data.py  reads tests/cassettes, writes src/data/cassettes.generated.ts
├── web/
│   ├── src/
│   │   ├── components/{ui,layout,sections}/
│   │   ├── data/cassettes.generated.ts    generated, never edited by hand
│   │   ├── hooks/
│   │   ├── styles/globals.css
│   │   └── config.ts       demo video URL and repo URL live here
│   └── index.html
├── .kiro/
│   ├── steering/{product,tech,structure}.md
│   ├── specs/ferric-core/{requirements,design,tasks}.md
│   └── hooks/{offline-guard,golden-tests,redaction-gate,spec-drift}.json
├── FRONTEND_SPEC.md
├── BUILD_GUIDE.md
├── APP_BLUEPRINT.md
├── MARKETING.md
├── CLAUDE.md
├── README.md
└── docs/HOW-THIS-WAS-BUILT.md
```

## Design System

All seven gates confirmed. Do not deviate from any value below. The full specification with exact classes, animation values and z-index stacks lives in FRONTEND_SPEC.md.

**Dials:** DESIGN_VARIANCE 8, MOTION_INTENSITY 8, VISUAL_DENSITY 5.

**Fingerprint:** top-left lead bottom-right support / compressed statement / monochrome plus single pop / technical grid / editorial stagger / scroll-driven narrative.

**Aesthetic:** bold brutalist, with Surveillance Design as the primary trend and Blueprint Design as the supporting trend. Surveillance contributes the monospace system-log language, timestamps and recorded-session framing. Blueprint contributes the annotated cassette schematic and the measurement-line treatment.

**Fonts:**
- Display: Big Shoulders Display, variable weight axis 400 to 900, used uppercase at large scale
- Body: Geist
- Mono: Martian Mono

```html
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@400..900&family=Geist:wght@300..600&family=Martian+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
```

Three families, the cap. Never Inter as display. Never Instrument Serif, Fraunces, Space Grotesk, Outfit or JetBrains Mono anywhere in this project.

**Colour palette, graphite and bone with amber pop:**
```css
--bg-primary:     #0b0b0c;
--bg-secondary:   #121214;
--bg-surface:     #17171a;
--bg-elevated:    #1e1e22;
--accent:         #ffb020;
--accent-hover:   #ffc352;
--accent-glow:    rgba(255, 176, 32, 0.12);
--text-primary:   #ededea;
--text-secondary: #9a9a94;
--text-muted:     #5c5c57;
--border-subtle:  rgba(255, 255, 255, 0.06);
--border-default: rgba(255, 255, 255, 0.11);
--border-strong:  rgba(255, 255, 255, 0.18);
--signal-fail:    #ff5c46;
```

Colour strategy is Restrained. Amber is the record light, so the accent carries meaning rather than taste. **Green does not exist in this system.** A passing assertion renders as quiet bone text. `--signal-fail` appears in exactly three places, all real failures from real cassettes: the diverged row in the Recorder section, the failed assertion in the Assertions section, and the diverged column in the drift report.

**Radius:** everything is `rounded-none` except the two nav pills and the record dot, which are `rounded-full`. Bold brutalist means hard corners. Never mix radius scales.

**Shadows:** none, anywhere, with one exception. The drift report's sticky filter bar carries `0 8px 24px -12px rgba(0,0,0,0.6)`. No outer glows ever.

**Nav:** A4 dual-pill split. Left pill carries a live session timecode, right pill carries three links and the GitHub CTA. Nothing across the centre.

**Background:** static but atmospheric. CSS technical grid in the hero and the Anatomy section only, inline SVG noise grain fixed page-wide, no ambient background animation anywhere.

**Motion:** one GSAP pinned sequence in the Recorder section, staggered blur-in reveals everywhere else, `once: false` on every single scroll animation with zero exceptions.

## No Logo, No Wordmark, No Brand Mark

This is a design decision, not a pending asset. Do not add one, do not leave a slot for one, do not generate a symbol, do not use an emoji.

The nav carries a live session timecode counting up from 00:00:00, driven by one `requestAnimationFrame` loop writing to a ref, never to React state. It does real work and it is what a recording device puts in that corner.

The footer closes on a statement of what the tool does, set large, not a name.

The name appears exactly three times on the site: the browser tab title, the install command in the Install section, and the footer sign-off. Each appearance is functional.

The favicon is an inline SVG data URI, one amber dot on graphite, hex values taken directly from the palette:
```html
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%230b0b0c'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%23ffb020'/%3E%3C/svg%3E" />
```

## Landing Page Sections, in order

1. **Nav**, A4 dual-pill split, session timecode left
2. **Hero**, headline top-left, live recorder readout bottom-right, technical grid
3. **The untested layer**, full-width typographic statement, scroll-driven weight shift
4. **The recorder**, GSAP pinned three-phase sequence, record then replay then drift
5. **What you can assert**, tabbed feature explorer, four assertion families
6. **Cassette anatomy**, asymmetric bento grid with a Blueprint schematic, six cells
7. **Install**, command-led convert section
8. **Footer**

Seven distinct layout families across eight sections. Two eyebrows total. No two consecutive sections share a layout family.

## Kiro Integration

Kiro Usage carries 20 of the 100 points and the README and demo video must both show meaningful use. Ferric's answer has three parts.

**Specs drive the build.** `.kiro/specs/ferric-core/` holds requirements written as acceptance criteria, a design document, and nineteen tasks mapped day by day. Every task references the criteria it satisfies. The specs were written before any code, and the day one session is screen-recorded for the demo video opening.

**Four hooks enforce the invariants.** `offline-guard` blocks a network call entering the default test suite. `golden-tests` reruns adapter goldens when the schema changes. `redaction-gate` stops an unredacted cassette entering version control. `spec-drift` is an agent-prompt hook that fires after each task and forces the spec to stay honest about what is actually satisfied.

**Ferric records Kiro.** The MCP adapter records the tool calls Kiro makes while building Ferric. Those cassettes ship as the demo fixture in `examples/demo-agent/`. The tool proving itself and the sponsor integration are the same scene in the video. This is the single highest-leverage decision in the project.

## Authenticity Rules, non-negotiable

The hackathon runs a pass-or-fail eligibility and viability screen before scoring. Failing it removes the entry rather than costing points. Three rules make that structurally impossible.

**Every displayed value traces to a real cassette.** `tests/cassettes/` is the single source of truth. `scripts/build_site_data.py` reads it and generates `web/src/data/cassettes.generated.ts`. Every section imports from that file. Nothing is typed by hand into a component. If a cassette does not exist at build time, the section holds its skeleton shimmer state permanently rather than inventing a number.

**Nothing is a screenshot.** The pinned sequence, all four assertion panels, the schematic, the hero readout and the entire report viewer are live DOM. There is no raster image of a terminal, a diff or a UI anywhere. The favicon is the only image on any surface.

**Limitations are stated on the marketing page.** Section 6 Cell F names what is not built. It is not an apology and not filler. It makes every other claim read as measured.

Anything that cannot satisfy all three by day seven gets cut from the page and listed in Cell F, not shipped weakened.

## Code Rules, follow without exception

**Python:**
- snake_case, type hints on every public function
- Docstrings on every module, class and public function
- pydantic validates at the boundary, never trust an unvalidated payload
- Provider SDKs import lazily inside adapters, never at package import time
- When the choice is a dependency or forty lines of standard library, choose the standard library
- No network access in the default test suite. A test that needs a provider lives in the separate drift suite, excluded from the default run

**TypeScript and React:**
- camelCase for variables and functions, PascalCase for components
- JSDoc on every function and custom hook
- No inline styles except dynamic values from `useMotionValue` or `useTransform`, and the `stroke-dashoffset` on the schematic leader lines
- CSS variables used directly, never hardcoded hex in a component
- `motion/react` for all animation, never `framer-motion`
- Blur-in entrance: `initial={{ opacity: 0, filter: 'blur(10px)', y: 24 }}`
- `viewport={{ once: false, amount: 0.1 }}` on every `whileInView`, zero exceptions
- CSS class hover states only, no `onMouseEnter` or `onMouseLeave` setting styles
- Magnetic hover uses `useMotionValue`, never `useState`
- GSAP only inside `Recorder.tsx`, registered once, every ScrollTrigger killed on unmount
- `min-h-[100dvh]`, never `h-screen`
- Backdrop blur only on fixed or sticky elements
- Icons are inline hand-written SVG in `Icon.tsx`, no icon library, no emoji

**Writing rules, apply to all copy, labels, comments, docstrings and every project document:**
- British English throughout
- No em dashes anywhere
- Periods and commas only where the sentence needs them
- Short direct sentences
- No filler: elevate, seamless, unlock, empower, revolutionise, transform, cutting-edge, next-gen, supercharge, streamline, leverage, discover
- CTA text is direct: "See it catch a regression", "View on GitHub", "Read the docs"
- Empty and loading states are honest: skeleton shimmer, never a spinner, never an invented number

**Never do these:**
- Never add a logo, wordmark, favicon file or brand mark
- Never use green anywhere in the palette
- Never present a screenshot as working functionality
- Never type a cassette value by hand into a component
- Never use `viewport={{ once: true }}`
- Never use a CSS keyframe animation with `animation-fill-mode: forwards` for a scroll reveal
- Never commit a cassette that has not passed the redaction gate
- Never let the default test suite touch the network
- Never claim a feature in the README that is not implemented

## Hackathon Checklist

- Project name: Ferric
- Hackathon: Ready, Spec, Ship, sponsored by Kiro
- Submission deadline: 23 August 2026, 23:59 UTC
- Submitted through the official Google Form: repository link, demo video link, project details
- Public repository required, and it must include the `.kiro` directory
- Complete README with setup and testing instructions required
- Demo video required, uploaded to YouTube, unlisted is acceptable
- Working application or test build a judge can run without paying
- Rubric: Application Quality 40, Kiro Usage 20, Documentation 20, Innovation and Potential 15, Presentation 5
- Pass-or-fail screen before scoring: eligibility, viability, and no simulated features presented as working
