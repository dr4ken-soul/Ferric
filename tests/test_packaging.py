from __future__ import annotations

import tomllib
from pathlib import Path


def test_base_install_declares_pytest_and_readme() -> None:
    pyproject = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    project = pyproject["project"]
    assert project["readme"] == "README.md"
    assert any(
        dependency.startswith("pytest>=") for dependency in project["dependencies"]
    )
    assert "dev" in project["optional-dependencies"]
