#!/usr/bin/env python3
"""
Validate pyproject.toml for common issues:
- Duplicate elements in list fields (keywords, classifiers, dependencies, extras)
- Invalid self-referencing extras (e.g., package[extra] inside its own extras)

Exit code:
- 0 on success
- 1 on validation failure
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    print("Python 3.11+ required (tomllib)", file=sys.stderr)
    sys.exit(1)

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def load_pyproject() -> dict:
    try:
        return tomllib.loads(PYPROJECT.read_text())
    except Exception as e:  # pragma: no cover
        print(f"Error parsing pyproject.toml: {e}", file=sys.stderr)
        sys.exit(1)


def find_duplicate_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    dups: set[str] = set()
    for x in items:
        if x in seen:
            dups.add(x)
        else:
            seen.add(x)
    return sorted(dups)


def check_list_for_dups(section_path: str, arr: list[object]) -> list[str]:
    if not all(isinstance(x, str) for x in arr):
        return []
    dups = find_duplicate_strings(arr)  # type: ignore[arg-type]
    return [f"{section_path}: duplicate entries -> {', '.join(dups)}"] if dups else []


def validate_extras(project: dict) -> list[str]:
    errors: list[str] = []
    opt = project.get("optional-dependencies", {})
    if not isinstance(opt, dict):
        return errors

    # Warn on clearly invalid self-references like "career-copilot[ai]" in extras
    project_name = project.get("name")
    for extra_name, arr in opt.items():
        if not isinstance(arr, list):
            continue
        for dep in arr:
            if isinstance(dep, str) and project_name and project_name in dep and "[" in dep:
                errors.append(
                    f"optional-dependencies.{extra_name}: self-referencing extra '{dep}' is invalid; list flattened deps instead"
                )
        errors.extend(check_list_for_dups(f"optional-dependencies.{extra_name}", arr))
    return errors


def main() -> int:
    data = load_pyproject()
    project = data.get("project", {})
    errors: list[str] = []

    # Check top-level project arrays
    for key in ("keywords", "classifiers", "dependencies"):
        arr = project.get(key)
        if isinstance(arr, list):
            errors.extend(check_list_for_dups(key, arr))

    # Check extras
    errors.extend(validate_extras(project))

    if errors:
        print("pyproject.toml validation failed:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("pyproject.toml validation passed: no duplicates or invalid extras detected")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
