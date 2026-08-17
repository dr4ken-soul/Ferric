export interface DocTopic {
  slug: string
  title: string
  summary: string
  paragraphs: string[]
  code?: { language: string; value: string }
  note?: string
}

export interface DocGroup {
  label: string
  slug: string
  topics: DocTopic[]
}

export const docGroups: DocGroup[] = [
  {
    label: 'Start',
    slug: 'start',
    topics: [
      {
        slug: 'install',
        title: 'Install',
        summary: 'Install the command and Python package with one name.',
        paragraphs: ['Ferric requires Python 3.11 or later. The package includes the wrapper, cassette store, assertion helpers, and command line interface.', 'Clone the public repository and install it into the active environment. This project is not presented as a published package.'],
        code: { language: 'shell', value: 'git clone https://github.com/dr4ken-soul/Ferric.git\ncd Ferric\npython -m pip install -e .\nferric verify' },
      },
      {
        slug: 'quickstart',
        title: 'Quickstart',
        summary: 'Record one interaction, then replay it without a provider connection.',
        paragraphs: ['Wrap the client at its construction point. Run the interaction once in record mode, then set replay mode for the test suite.', 'The application receives the provider response in record mode and the recorded response in replay mode. Call sites do not change between the two.'],
        code: { language: 'python', value: 'import ferric\n\nclient = ferric.wrap(client)\n# Run once with FERRIC_MODE=record\n# Test with FERRIC_MODE=replay' },
      },
      {
        slug: 'how-replay-works',
        title: 'How replay works',
        summary: 'Replay matches a normalised request fingerprint and never falls through to a provider.',
        paragraphs: ['The matcher builds a fingerprint from the model, normalised messages, and tool definitions in scope. Volatile request identifiers and timestamps are excluded.', 'A match returns the recorded provider response. No provider SDK transport is called. An unmatched request is a hard failure with the nearest cassette shown for diagnosis.'],
        note: 'Replay is hermetic by design. It never opens a provider socket and never makes a live fallback request.',
      },
    ],
  },
  {
    label: 'Record',
    slug: 'record',
    topics: [
      {
        slug: 'wrapping-a-client',
        title: 'Wrapping a client',
        summary: 'Adopt recording at the client boundary without rewriting model calls.',
        paragraphs: ['The wrapper forwards requests and responses without changing their public shape. Provider errors are recorded as error events and then raised again.', 'Keep the wrapper close to client construction. This gives record and replay modes one stable boundary.'],
        code: { language: 'python', value: 'from openai import OpenAI\nimport ferric\n\nclient = ferric.wrap(OpenAI())' },
      },
      {
        slug: 'adapters',
        title: 'Adapters',
        summary: 'Adapters map provider payloads onto one ordered event schema.',
        paragraphs: ['OpenAI, Anthropic, and MCP tool calls are the supported adapter surfaces. Provider packages load lazily, so an unused provider is not required at import time.', 'Each adapter emits user, assistant, tool call, tool result, and error events. Assertions operate on these normalised events rather than raw HTTP bodies.'],
      },
      {
        slug: 'redaction',
        title: 'Redaction',
        summary: 'Secrets are removed before cassette bytes reach disk.',
        paragraphs: ['Built-in rules cover API keys, bearer tokens, email addresses, and card numbers. Project rules can add domain-specific patterns.', 'Every removal creates a redaction record with the rule class, event index, and field path. The removed value is never written to the cassette or command output.'],
        code: { language: 'json', value: '{\n  "rule_class": "bearer_token",\n  "event_index": "<event-index>",\n  "field_path": "payload.content"\n}' },
      },
    ],
  },
  {
    label: 'Replay',
    slug: 'replay',
    topics: [
      {
        slug: 'matching',
        title: 'Matching',
        summary: 'Stable inputs form a content fingerprint for deterministic lookup.',
        paragraphs: ['Model identity, normalised messages, and available tool definitions take part in matching. The exact ordering of messages and tools is retained.', 'Timestamps and provider request identifiers are left out because they change without changing the requested behaviour.'],
      },
      {
        slug: 'unmatched-requests',
        title: 'Unmatched requests',
        summary: 'A missing fingerprint stops the run and reports the nearest recorded request.',
        paragraphs: ['A prompt edit, model change, or tool definition change can make a request unmatched. The exception includes the requested fingerprint and the nearest cassette by fingerprint distance.', 'There is no permissive mode and no live fallback. Record the intended interaction explicitly when the change is valid.'],
      },
      {
        slug: 'ci-setup',
        title: 'CI setup',
        summary: 'Set replay mode for the default suite and keep provider credentials out of the job.',
        paragraphs: ['Commit redacted cassettes beside the tests that consume them. Run verification before pytest so malformed or unsafe evidence fails early.', 'The drift suite is separate because it is the only workflow that needs network access and a provider key.'],
        code: { language: 'yaml', value: '- run: ferric verify\n- run: pytest\n  env:\n    FERRIC_MODE: replay' },
      },
    ],
  },
  {
    label: 'Assert',
    slug: 'assert',
    topics: [
      {
        slug: 'sequence',
        title: 'Sequence',
        summary: 'Compare ordered tool names and report the first changed position.',
        paragraphs: ['Sequence assertions ignore response wording and inspect agent behaviour. A failure prints the cassette identifier, expected order, observed order, and divergence index.'],
        code: { language: 'python', value: 'assert_tool_sequence(\n    cassette,\n    ["<first-tool>", "<second-tool>"],\n)' },
      },
      {
        slug: 'arguments',
        title: 'Arguments',
        summary: 'Match only the fields that are critical to application behaviour.',
        paragraphs: ['Declare the tool and fields whose values must stay exact. Other fields can change without making the assertion noisy.', 'Missing fields, changed types, and changed values are reported with expected and observed values.'],
        code: { language: 'python', value: 'assert_tool_arguments(\n    cassette,\n    tool="<tool-name>",\n    critical={"<field>": "<expected-value>"},\n)' },
      },
      {
        slug: 'schema',
        title: 'Schema',
        summary: 'Validate structured assistant output and report the failing JSON path.',
        paragraphs: ['Schema assertions check parsed output against the declared JSON schema. A failure identifies the exact path and type mismatch instead of returning one boolean.'],
        code: { language: 'python', value: 'assert_response_schema(cassette, anomaly_report_schema)' },
      },
      {
        slug: 'leakage',
        title: 'Leakage',
        summary: 'Check outbound requests for declared secret or personal-data patterns.',
        paragraphs: ['Leakage assertions scan outbound request events. They complement write-path redaction by making unsafe prompt construction a test failure.', 'The failure names the pattern and field path without printing the matched secret.'],
        code: { language: 'python', value: 'assert_no_leakage(cassette, patterns=[bearer_pattern])' },
      },
    ],
  },
  {
    label: 'Commands',
    slug: 'commands',
    topics: [
      {
        slug: 'promote',
        title: 'promote',
        summary: 'Turn a recorded trace into a redacted runnable regression test.',
        paragraphs: ['Promotion reads the trace, applies redaction, writes a cassette, and emits a test with default behavioural assertions. The generated test is intended to run without hand editing.'],
        code: { language: 'shell', value: 'ferric promote <trace-id>' },
      },
      {
        slug: 'drift',
        title: 'drift',
        summary: 'Run the cassette library against a target model and classify behavioural movement.',
        paragraphs: ['Drift is the only command that calls a live provider. Results are classified as unchanged, reworded, or behaviourally changed, with the moved dimension named.', 'The optional HTML output is a self-contained report. The command reports token spend because this check has a real provider cost.'],
        code: { language: 'shell', value: 'ferric drift --to <model> --html report.html' },
      },
      {
        slug: 'list',
        title: 'list',
        summary: 'Inspect cassette identifiers, providers, models, and event counts.',
        paragraphs: ['Listing reads the local store only. Use it to confirm which evidence is available before selecting a trace or running a focused test.'],
        code: { language: 'shell', value: 'ferric list' },
      },
      {
        slug: 'verify',
        title: 'verify',
        summary: 'Validate schema integrity, event order, identifiers, and redaction safety.',
        paragraphs: ['Verification fails the whole run when a cassette is corrupt or unsafe. It is suitable as the first cassette-related CI step.'],
        code: { language: 'shell', value: 'ferric verify' },
      },
    ],
  },
  {
    label: 'Reference',
    slug: 'reference',
    topics: [
      {
        slug: 'cassette-format',
        title: 'Cassette format',
        summary: 'Each interaction is plain JSON with a content-derived identifier.',
        paragraphs: ['A cassette stores its identifier, provider, model, recording time, request fingerprint, ordered events, and redaction records. The identifier is based on normalised event content, so formatting changes do not alter it.', 'Files are designed to be readable in pull request review and portable between machines.'],
        code: { language: 'json', value: '{\n  "id": "<content-hash>",\n  "provider": "<provider>",\n  "model": "<model>",\n  "fingerprint": "<request-hash>",\n  "events": [],\n  "redactions": []\n}' },
      },
      {
        slug: 'event-schema',
        title: 'Event schema',
        summary: 'Five event roles describe the interaction in one monotonic sequence.',
        paragraphs: ['User, assistant, tool call, tool result, and error events share an integer index, role, and payload object. Indices must be unique and monotonic within a cassette.', 'Tool call payloads carry a tool name and arguments. Provider-specific fields remain inside the normalised payload only when assertions or replay require them.'],
      },
      {
        slug: 'limitations',
        title: 'Limitations',
        summary: 'The current scope favours reliable text and tool traffic over broad endpoint coverage.',
        paragraphs: ['Streaming responses are coalesced into one assistant message rather than captured token by token. Embeddings, image, and audio endpoints are not supported.', 'There is no hosted service, dashboard, account system, automatic assertion generation beyond promotion defaults, or branching replay of divergent conversations. Provider coverage is limited to OpenAI, Anthropic, and MCP tool calls.'],
        note: 'These are current product boundaries. Unsupported traffic should not be presented as recorded or replayed evidence.',
      },
    ],
  },
]

export const allDocTopics = docGroups.flatMap((group) => group.topics.map((topic) => ({ ...topic, group: group.label })))
