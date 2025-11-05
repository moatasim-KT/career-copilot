#!/usr/bin/env python3
"""
Script to convert all API endpoints from synchronous Session to AsyncSession
"""

import re
from pathlib import Path


def convert_file(file_path):
    """Convert a single file to use AsyncSession"""
    with open(file_path) as f:
        content = f.read()

    original_content = content
    changes_made = []

    # 1. Replace import statements
    if "from sqlalchemy.orm import Session" in content:
        content = content.replace(
            "from sqlalchemy.orm import Session",
            "from sqlalchemy.ext.asyncio import AsyncSession",
        )
        changes_made.append("Updated Session import")

    # 2. Add select import if using AsyncSession
    if "AsyncSession" in content and "from sqlalchemy import select" not in content:
        # Find where to add the import
        if "from sqlalchemy import" in content:
            content = re.sub(
                r"from sqlalchemy import ([^\n]+)",
                r"from sqlalchemy import select, \1",
                content,
                count=1,
            )
            changes_made.append("Added select import")

    # 3. Replace Session type hints
    content = re.sub(
        r"db:\s*Session\s*=\s*Depends\(get_db\)",
        r"db: AsyncSession = Depends(get_db)",
        content,
    )
    if "AsyncSession = Depends(get_db)" in content:
        changes_made.append("Converted Session to AsyncSession in function signatures")

    # 4. Add note about async conversion needed
    if changes_made and "# TODO: Convert to async queries" not in content:
        # Add a comment at the top after imports
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("router = APIRouter") or line.startswith("@router"):
                lines.insert(
                    i, "# NOTE: This file has been converted to use AsyncSession."
                )
                lines.insert(
                    i + 1,
                    "# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)",
                )
                lines.insert(i + 2, "")
                content = "\n".join(lines)
                break

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True, changes_made
    return False, []


def main():
    """Convert all API files"""
    api_dir = Path("app/api/v1")
    converted_files = []

    for py_file in api_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        changed, changes = convert_file(py_file)
        if changed:
            converted_files.append((py_file.name, changes))
            print(f"✓ Converted {py_file.name}: {', '.join(changes)}")

    print(f"\n{'=' * 60}")
    print(f"Converted {len(converted_files)} files to use AsyncSession")
    print(f"{'=' * 60}")
    print("\nIMPORTANT: Database queries still need manual conversion!")
    print("Replace: db.query(Model).filter(...).first()")
    print("   With: result = await db.execute(select(Model).where(...))")
    print("         item = result.scalar_one_or_none()")


if __name__ == "__main__":
    main()
