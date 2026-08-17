"""Reject network and provider imports from Ferric's default test suite."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_ROOT = PROJECT_ROOT / "tests"
FORBIDDEN_IMPORTS = frozenset(
    {
        "aiohttp",
        "anthropic",
        "azure.ai.inference",
        "boto3",
        "botocore",
        "cohere",
        "google.genai",
        "google.generativeai",
        "groq",
        "httpx",
        "mistralai",
        "openai",
        "replicate",
        "requests",
        "socket",
        "urllib",
    }
)


@dataclass(frozen=True)
class ImportViolation:
    """Describe one forbidden import without including source contents."""

    path: Path
    line: int
    module: str


def is_drift_test(path: Path, project_root: Path = PROJECT_ROOT) -> bool:
    """Return whether a path is inside the permitted tests/drift suite."""

    try:
        relative = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return False
    parts = tuple(part.casefold() for part in relative.parts)
    return len(parts) >= 2 and parts[0:2] == ("tests", "drift")


def iter_python_files(paths: Iterable[Path]) -> list[Path]:
    """Return unique Python files found beneath files and directories."""

    files: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved.is_file() and resolved.suffix == ".py":
            files.add(resolved)
        elif resolved.is_dir():
            files.update(candidate.resolve() for candidate in resolved.rglob("*.py"))
    return sorted(files, key=lambda candidate: str(candidate).casefold())


def import_is_forbidden(module: str) -> bool:
    """Return whether a module is a known network or provider package."""

    return any(
        module == forbidden or module.startswith(f"{forbidden}.")
        for forbidden in FORBIDDEN_IMPORTS
    )


def find_forbidden_imports(path: Path) -> list[ImportViolation]:
    """Parse one Python file and return its forbidden imports."""

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    violations: list[ImportViolation] = []

    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
            modules.extend(f"{node.module}.{alias.name}" for alias in node.names)
        else:
            continue

        for module in modules:
            if import_is_forbidden(module):
                violations.append(ImportViolation(path, node.lineno, module))
                break

    return violations


def scan_paths(paths: Iterable[Path]) -> tuple[list[ImportViolation], list[str]]:
    """Scan paths and return import violations plus safe parse errors."""

    violations: list[ImportViolation] = []
    errors: list[str] = []
    for path in iter_python_files(paths):
        if is_drift_test(path):
            continue
        try:
            violations.extend(find_forbidden_imports(path))
        except (OSError, UnicodeError, SyntaxError) as error:
            errors.append(f"{path}: cannot scan: {type(error).__name__}")
    return violations, errors


def main(argv: Sequence[str] | None = None) -> int:
    """Run the offline import gate and return a process exit code."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    paths = [Path(argument) for argument in arguments] or [DEFAULT_TEST_ROOT]
    violations, errors = scan_paths(paths)

    for violation in violations:
        try:
            display_path = violation.path.relative_to(PROJECT_ROOT)
        except ValueError:
            display_path = violation.path
        print(
            f"{display_path}:{violation.line}: forbidden import "
            f"{violation.module!r} in the default test suite"
        )
    for error in errors:
        print(error)

    if violations or errors:
        print("Offline guard failed. Move live-provider tests under tests/drift/.")
        return 1

    print("Offline guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
