# Technical Steering

## Runtime

- Python 3.11 or newer.
- `pydantic` validates events, cassettes, manifests and drift results at boundaries.
- `typer` provides the `ferric` command.
- `pytest`, `pytest-cov`, `ruff` and `mypy` form the development toolchain.
- Cassettes are plain JSON with identifiers derived from the normalised event list.
- Prefer the standard library when it avoids a small dependency.

The distribution, import package, CLI entry point and source directory are all named `ferric`.

## Runtime Modes

`FERRIC_MODE` accepts `record`, `replay`, or an unset passthrough mode. Record mode calls the wrapped provider, normalises the result and writes a redacted cassette. Replay mode resolves a fingerprint against the cassette store and must not construct or call a provider transport. Passthrough mode adds one function call and otherwise preserves client behaviour.

Provider SDK imports are lazy and live inside adapter functions. Importing `ferric` must not import OpenAI, Anthropic or another provider package.

## Python Rules

- Use snake_case.
- Add type hints to every public function.
- Add docstrings to every module, class and public function.
- Validate untrusted payloads before use.
- Write errors to the cassette before re-raising them.
- Do not emit raw matched secrets in exceptions or logs.
- Keep live-provider drift tests under `tests/drift/` and exclude that directory from the default suite.
- The default suite must not import network clients, socket modules or provider SDKs.

## Web Stack

- React 18, Vite and TypeScript.
- Tailwind CSS mapped to the variables in `FRONTEND_SPEC.md`.
- `motion/react` for general animation.
- GSAP ScrollTrigger only inside `Recorder.tsx`, with complete cleanup on unmount.
- A static deployment on Vercel or Netlify. There is no backend.
- The drift report is one HTML file with inline CSS, inline vanilla JavaScript and no external request.

All site values that describe cassettes come from `tests/cassettes/` through `scripts/build_site_data.py`. Components must not contain copied cassette values.

## Frontend Invariants

- Use the graphite, bone, amber and failure palette exactly as specified.
- Do not use green.
- Use hard corners except for nav pills and status dots.
- Do not use a logo, wordmark lockup, icon library, raster product screenshot or hardcoded component hex value.
- Use `min-h-[100dvh]`, never `h-screen`.
- Every `whileInView` uses `viewport={{ once: false, amount: 0.1 }}` unless the specification gives a different amount.
- Reduced motion disables pins, blur, translation, magnetic movement and scroll-driven weight changes.
- Loading states use skeleton shimmer and never invented values.

## Quality Gates

Run the offline import scanner on default-suite test changes. Run adapter golden tests after schema or adapter changes. Run the redaction scanner on cassette changes. Validate requirements and task evidence after each completed task. Before submission, run `ruff`, `mypy`, the default pytest suite, `ferric verify`, the two guard scripts and a clean-machine replay check.

## Writing

Use British English, short direct sentences and no em dashes. Do not claim unimplemented behaviour. Public copy and technical documents follow the same rules.
