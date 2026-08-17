# Product Steering

## Product

Ferric is a local flight recorder for LLM and agent traffic. A developer wraps an existing client in one line, records a normalised interaction cassette, and replays it in CI without a provider call. Assertions examine behaviour rather than exact prose.

The primary user is a backend or platform engineer maintaining an AI feature inside an existing pytest suite. Teams preparing a model upgrade are the second audience. A judge must also be able to prove the core workflow from a clean clone, without an API key, in under two minutes.

## Product Promise

Your AI feature has no test suite. Ferric is the one it should have had.

Ferric must provide:

1. Transparent capture that preserves request and response behaviour.
2. Hermetic replay that cannot fall through to a live provider.
3. Safe promotion of a recorded trace into a runnable regression test.
4. Behavioural assertions for tool sequence, critical arguments, response schema and leakage.
5. Model drift classification with an offline, self-contained HTML report.

## Product Principles

- Evidence comes before claims. Displayed values must come from committed cassettes.
- Offline replay is the central guarantee. A missing match is a hard failure.
- Plain JSON keeps cassettes readable in a pull request.
- Errors are recorded and re-raised. Failure paths are part of the interaction.
- Secrets are removed before a cassette reaches disk. Logs must not repeat matched values.
- Passing behaviour is quiet. Failures identify the cassette and divergence point.
- A clean clone must run the default suite without a key or network access.

## Scope

The competition scope includes OpenAI, Anthropic and MCP adapters, record and replay modes, promotion, four assertion families, drift analysis, a self-contained report, a static landing page, a docs route and a runnable demo fixture.

The competition scope excludes token-by-token streaming capture, embeddings, image and audio endpoints, hosted services, accounts, payments, automatic assertion generation beyond promotion defaults, multi-turn branching and providers outside OpenAI, Anthropic and MCP.

## Authenticity

`tests/cassettes/` is the source of truth for product demonstrations. The web build generates its displayed cassette data from those files. Missing evidence produces a skeleton state, not invented data. Product interfaces are live DOM, not screenshots. Limitations are stated in the landing page, README and docs.

## Success Measures

- Record then replay returns byte-identical content.
- Replay opens no provider socket and uses no API key.
- A promoted test runs without manual edits.
- Assertion failures identify the exact divergence.
- Every committed cassette passes schema and redaction checks.
- The demo workflow completes from a clean clone in under two minutes.
