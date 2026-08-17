"""Typer command surface for Ferric cassette workflows."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Annotated, Any, NoReturn

import typer

from ferric.drift import DriftProviderError, run_drift
from ferric.report import write_drift_report
from ferric.schema import EventRole
from ferric.store import CassetteStore, CassetteStoreError

app = typer.Typer(
    add_completion=False,
    help="Record, replay and verify LLM interaction cassettes.",
    no_args_is_help=True,
)


def _store(path: Path | None) -> CassetteStore:
    return CassetteStore(path)


def _abort(error: BaseException) -> NoReturn:
    typer.echo(f"Error: {error}")
    raise typer.Exit(code=1)


@app.command("list")
def list_cassettes(
    cassette_dir: Annotated[
        Path | None,
        typer.Option("--cassette-dir", help="Cassette library directory."),
    ] = None,
) -> None:
    """List validated cassettes without network access."""

    try:
        cassettes = _store(cassette_dir).list()
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
) -> None:
    """Validate cassette schemas, identifiers, manifests and redaction."""

    try:
        cassettes = _store(cassette_dir).verify()
    except CassetteStoreError as error:
        _abort(error)
    typer.echo(
        f"Verified {len(cassettes)} cassette(s). Schema, hashes and redaction passed."
    )


def _promotion_source(cassette_dir: Path | None) -> CassetteStore:
    if cassette_dir is not None:
        return CassetteStore(cassette_dir)
    configured = os.environ.get("FERRIC_TRACE_DIR")
    return CassetteStore(Path(configured) if configured else Path(".ferric/cassettes"))


def _generated_test(cassette: Any, cassette_path: Path) -> str:
    relative = cassette_path.as_posix()
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
        "from ferric.schema import Cassette",
        "",
        "",
        "def test_promoted_interaction() -> None:",
        '    """Replay the promoted interaction assertions offline."""',
        f"    cassette = Cassette.model_validate_json(Path({relative!r}).read_text(encoding='utf-8'))",
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
    lines.append("    assert_no_leakage(cassette, {})")
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
) -> None:
    """Promote a recorded trace into a redacted runnable pytest test."""

    try:
        cassette = _promotion_source(cassette_dir).read(trace_id)
    except CassetteStoreError as error:
        _abort(error)
    cassette_root = output_dir / "cassettes"
    destination_store = CassetteStore(cassette_root)
    safe_id = cassette.id
    existed = (cassette_root / f"{safe_id}.json").exists()
    safe = destination_store.write(cassette)
    test_path = output_dir / f"test_promoted_{safe.id[:12]}.py"
    content = _generated_test(safe, cassette_root / f"{safe.id}.json")
    output_dir.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output_dir, prefix=f".{test_path.name}.", suffix=".tmp", text=True
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, test_path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        if not existed:
            destination_store.delete(safe.id)
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
) -> None:
    """Call a live provider and report model drift for the cassette library."""

    store = _store(cassette_dir)
    try:
        cassettes = store.verify()
        results = run_drift(store, target_model)
    except (CassetteStoreError, DriftProviderError) as error:
        _abort(error)
    counts = {
        state: sum(result.classification.value == state for result in results)
        for state in ("unchanged", "reworded", "diverged")
    }
    total_tokens = sum(result.tokens_spent for result in results)
    typer.echo(
        f"unchanged {counts['unchanged']} | reworded {counts['reworded']} | "
        f"diverged {counts['diverged']} | tokens {total_tokens}"
    )
    for result in results:
        dimension = f" ({result.dimension.value})" if result.dimension else ""
        typer.echo(
            f"{result.cassette_id[:12]} {result.classification.value}{dimension}"
        )
    if html_path is not None:
        baseline = cassettes[0].model if cassettes else "none"
        write_drift_report(
            html_path,
            results,
            baseline_model=baseline,
            target_model=target_model,
        )
        typer.echo(f"Wrote {html_path}.")


def main() -> None:
    """Run the Ferric command application."""

    app()


if __name__ == "__main__":
    main()
