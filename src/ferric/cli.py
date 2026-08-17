"""Typer command surface for Ferric cassette workflows."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Annotated, Any, Literal, NoReturn, cast

import typer

from ferric.drift import DriftProviderError, run_drift
from ferric.redact import RedactionRule
from ferric.report import write_drift_report
from ferric.schema import EventRole
from ferric.store import CassetteStore, CassetteStoreError

app = typer.Typer(
    add_completion=False,
    help="Record, replay and verify LLM interaction cassettes.",
    no_args_is_help=True,
)
_replace = os.replace


def _rules(values: list[str]) -> tuple[RedactionRule, ...]:
    rules: list[RedactionRule] = []
    for value in values:
        try:
            name, pattern = value.split("=", 1)
            rules.append(RedactionRule.from_pattern(name, pattern))
        except (ValueError, TypeError, re.error):
            _abort(ValueError("custom rules must use NAME=REGEX"))
    return tuple(rules)


def _store(path: Path | None, custom_rule: list[str] | None = None) -> CassetteStore:
    return CassetteStore(path, _rules(custom_rule or []))


def _abort(error: BaseException) -> NoReturn:
    typer.echo(f"Error: {error}")
    raise typer.Exit(code=1)


@app.command("list")
def list_cassettes(
    cassette_dir: Annotated[
        Path | None,
        typer.Option("--cassette-dir", help="Cassette library directory."),
    ] = None,
    custom_rule: Annotated[
        list[str] | None,
        typer.Option("--redact", help="Repeatable NAME=REGEX custom redaction rule."),
    ] = None,
) -> None:
    """List validated cassettes without network access."""

    try:
        cassettes = _store(cassette_dir, custom_rule).list()
    except CassetteStoreError as error:
        _abort(error)
    if not cassettes:
        typer.echo("No cassettes found.")
        return
    typer.echo("ID            PROVIDER    MODEL                   EVENTS")
    for cassette in cassettes:
        typer.echo(
            f"{cassette.id[:12]:<12}  {cassette.provider:<10}  "
            f"{cassette.model:<22}  {len(cassette.events)}"
        )


@app.command()
def verify(
    cassette_dir: Annotated[
        Path | None,
        typer.Option("--cassette-dir", help="Cassette library directory."),
    ] = None,
    custom_rule: Annotated[
        list[str] | None,
        typer.Option("--redact", help="Repeatable NAME=REGEX custom redaction rule."),
    ] = None,
) -> None:
    """Validate cassette schemas, identifiers, manifests and redaction."""

    try:
        cassettes = _store(cassette_dir, custom_rule).verify()
    except CassetteStoreError as error:
        _abort(error)
    typer.echo(
        f"Verified {len(cassettes)} cassette(s). Schema, hashes and redaction passed."
    )


def _promotion_source(
    cassette_dir: Path | None,
    custom_rules: tuple[RedactionRule, ...] = (),
) -> CassetteStore:
    if cassette_dir is not None:
        return CassetteStore(cassette_dir, custom_rules)
    configured = os.environ.get("FERRIC_CASSETTE_DIR")
    return CassetteStore(Path(configured) if configured else None, custom_rules)


def _generated_test(cassette: Any, cassette_path: Path) -> str:
    relative_parts = cassette_path.parts[-2:]
    tools = [
        event.payload for event in cassette.events if event.role is EventRole.TOOL_CALL
    ]
    lines = [
        '"""Generated Ferric regression test."""',
        "",
        "from pathlib import Path",
        "",
        "from ferric.assertions import (",
        "    assert_no_leakage,",
        "    assert_response_schema,",
        "    assert_tool_arguments,",
        "    assert_tool_sequence,",
        ")",
        "from ferric.redact import BUILT_IN_RULES",
        "from ferric.schema import Cassette",
        "",
        "",
        "def test_promoted_interaction() -> None:",
        '    """Replay the promoted interaction assertions offline."""',
        f"    cassette_path = Path(__file__).parent.joinpath({relative_parts[0]!r}, {relative_parts[1]!r})",
        "    cassette = Cassette.model_validate_json(cassette_path.read_text(encoding='utf-8'))",
        f"    assert_tool_sequence(cassette, {[tool.name for tool in tools]!r})",
    ]
    for index, tool in enumerate(tools):
        critical = {
            key: value
            for key, value in tool.arguments.items()
            if isinstance(value, (str, int, float, bool)) or value is None
        }
        lines.append(
            f"    assert_tool_arguments(cassette, {tool.name!r}, {critical!r}, occurrence={sum(previous.name == tool.name for previous in tools[:index])})"
        )
    assistants = [
        event.payload.content
        for event in cassette.events
        if event.role is EventRole.ASSISTANT
    ]
    if assistants and isinstance(assistants[-1], dict):
        properties = {
            key: {"type": _json_type(value)} for key, value in assistants[-1].items()
        }
        schema = {
            "type": "object",
            "properties": properties,
            "required": list(properties),
        }
        lines.append(f"    assert_response_schema(cassette, {schema!r})")
    lines.append(
        "    assert_no_leakage(cassette, {rule.rule_class: rule.pattern for rule in BUILT_IN_RULES})"
    )
    lines.append("")
    return "\n".join(lines)


def _json_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value is None:
        return "null"
    return "string"


@app.command()
def promote(
    trace_id: Annotated[str, typer.Argument(help="Trace identifier or prefix.")],
    cassette_dir: Annotated[
        Path | None,
        typer.Option("--cassette-dir", help="Recorded trace directory."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Destination test directory."),
    ] = Path("tests"),
    custom_rule: Annotated[
        list[str] | None,
        typer.Option("--redact", help="Repeatable NAME=REGEX custom redaction rule."),
    ] = None,
) -> None:
    """Promote a recorded trace into a redacted runnable pytest test."""

    try:
        rules = _rules(custom_rule or [])
        cassette = _promotion_source(cassette_dir, rules).read(trace_id)
    except CassetteStoreError as error:
        _abort(error)
    cassette_root = output_dir / "cassettes"
    destination_store = CassetteStore(cassette_root, rules)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = destination_store.redactor.redact_cassette(cassette)
    test_path = output_dir / f"test_promoted_{safe.id[:12]}.py"
    content = _generated_test(safe, cassette_root / f"{safe.id}.json")
    compile(content, str(test_path), "exec")
    cassette_existed = (cassette_root / f"{safe.id}.json").exists()
    manifest_existed = destination_store.manifest_path.exists()
    test_existed = test_path.exists()
    previous_test = test_path.read_bytes() if test_existed else None
    temporary_name: str | None = None
    try:
        safe = destination_store.write(safe)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=output_dir, prefix=f".{test_path.name}.", suffix=".tmp", text=True
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _replace(temporary_name, test_path)
    except BaseException:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
        if not cassette_existed and (cassette_root / f"{safe.id}.json").exists():
            destination_store.delete(safe.id)
            if not manifest_existed:
                try:
                    destination_store.manifest_path.unlink()
                except FileNotFoundError:
                    pass
        if test_existed and previous_test is not None:
            test_path.write_bytes(previous_test)
        elif not test_existed:
            try:
                test_path.unlink()
            except FileNotFoundError:
                pass
        raise
    typer.echo(f"Promoted {safe.id} to {test_path}.")


@app.command()
def drift(
    target_model: Annotated[str, typer.Option("--to", help="Target model identifier.")],
    html_path: Annotated[
        Path | None,
        typer.Option("--html", help="Write a self-contained HTML report."),
    ] = None,
    cassette_dir: Annotated[
        Path | None,
        typer.Option("--cassette-dir", help="Cassette library directory."),
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option("--provider", help="Target provider: openai or anthropic."),
    ] = None,
    custom_rule: Annotated[
        list[str] | None,
        typer.Option("--redact", help="Repeatable NAME=REGEX custom redaction rule."),
    ] = None,
) -> None:
    """Call a live provider and report model drift for the cassette library."""

    if provider not in {None, "openai", "anthropic"}:
        _abort(ValueError("provider must be openai or anthropic"))
    selected_provider = cast(Literal["openai", "anthropic"] | None, provider)
    store = _store(cassette_dir, custom_rule)
    try:
        cassettes = store.verify()
        run = run_drift(store, target_model, target_provider=selected_provider)
    except (CassetteStoreError, DriftProviderError) as error:
        _abort(error)
    counts = {
        state: sum(result.classification.value == state for result in run.results)
        for state in ("unchanged", "reworded", "diverged")
    }
    total_tokens = run.tokens_spent
    typer.echo(
        f"unchanged {counts['unchanged']} | reworded {counts['reworded']} | "
        f"diverged {counts['diverged']} | skipped {len(run.skipped)} | "
        f"tokens {total_tokens}"
    )
    for result in run.results:
        dimension = f" ({result.dimension.value})" if result.dimension else ""
        typer.echo(
            f"{result.cassette_id[:12]} {result.classification.value}{dimension}"
        )
    for skipped in run.skipped:
        typer.echo(f"{skipped.cassette_id[:12]} skipped ({skipped.reason})")
    if html_path is not None:
        baseline = cassettes[0].model if cassettes else "none"
        write_drift_report(
            html_path,
            run.results,
            baseline_model=baseline,
            target_model=target_model,
        )
        typer.echo(f"Wrote {html_path}.")


def main() -> None:
    """Run the Ferric command application."""

    app()


if __name__ == "__main__":
    main()
