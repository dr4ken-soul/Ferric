"""Reject sensitive values from Ferric cassette JSON files."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASSETTE_ROOT = PROJECT_ROOT / "tests" / "cassettes"
SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("api_key", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]+")),
    (
        "bearer_token",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    ),
    (
        "email",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    ),
    ("card", re.compile(r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)")),
)


@dataclass(frozen=True)
class RedactionViolation:
    """Describe sensitive data by class and location without exposing its value."""

    path: Path
    json_path: str
    rule_class: str


def iter_json_files(paths: Iterable[Path]) -> list[Path]:
    """Return unique JSON files found beneath files and directories."""

    files: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved.is_file() and resolved.suffix.casefold() == ".json":
            files.add(resolved)
        elif resolved.is_dir():
            files.update(candidate.resolve() for candidate in resolved.rglob("*.json"))
    return sorted(files, key=lambda candidate: str(candidate).casefold())


def walk_strings(value: Any, json_path: str = "$") -> Iterator[tuple[str, str]]:
    """Yield each scannable JSON value and its safe structural path."""

    if isinstance(value, str):
        yield json_path, value
    elif isinstance(value, int) and not isinstance(value, bool):
        yield json_path, str(value)
    elif isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            safe_key = (
                "<redacted-key>"
                if any(pattern.search(key_text) for _, pattern in SENSITIVE_PATTERNS)
                else key_text
            )
            yield f"{json_path}.<key>", key_text
            yield from walk_strings(child, f"{json_path}.{safe_key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_strings(child, f"{json_path}[{index}]")


def find_sensitive_values(path: Path) -> list[RedactionViolation]:
    """Parse one cassette and return sensitive value locations."""

    with path.open("r", encoding="utf-8") as cassette_file:
        payload = json.load(cassette_file)

    violations: list[RedactionViolation] = []
    for json_path, value in walk_strings(payload):
        for rule_class, pattern in SENSITIVE_PATTERNS:
            if pattern.search(value):
                violations.append(RedactionViolation(path, json_path, rule_class))
    return violations


def scan_paths(paths: Iterable[Path]) -> tuple[list[RedactionViolation], list[str]]:
    """Scan cassette paths and return violations plus safe parse errors."""

    violations: list[RedactionViolation] = []
    errors: list[str] = []
    for path in iter_json_files(paths):
        try:
            violations.extend(find_sensitive_values(path))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append(f"{path}: cannot scan: {type(error).__name__}")
    return violations, errors


def main(argv: Sequence[str] | None = None) -> int:
    """Run the cassette redaction gate and return a process exit code."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    paths = [Path(argument) for argument in arguments] or [DEFAULT_CASSETTE_ROOT]
    violations, errors = scan_paths(paths)

    for violation in violations:
        try:
            display_path = violation.path.relative_to(PROJECT_ROOT)
        except ValueError:
            display_path = violation.path
        print(
            f"{display_path}:{violation.json_path}: unredacted "
            f"{violation.rule_class} value"
        )
    for error in errors:
        print(error)

    if violations or errors:
        print("Redaction gate failed. Sensitive values were not printed.")
        return 1

    print("Redaction gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
