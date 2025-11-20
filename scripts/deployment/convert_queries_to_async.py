#!/usr/bin/env python3
"""
Script to convert synchronous SQLAlchemy queries to async pattern.
This handles the actual db.query() -> await db.execute(select()) conversion.
"""

import re
from pathlib import Path


def needs_select_import(content: str) -> bool:
    """Check if file already has select import"""
    return "from sqlalchemy import" in content and "select" not in content


def add_select_import(content: str) -> str:
    """Add select to existing sqlalchemy imports if needed"""
    if not needs_select_import(content):
        return content

    # Find the sqlalchemy import line
    pattern = r"from sqlalchemy import ([^\n]+)"
    match = re.search(pattern, content)
    if match:
        imports = match.group(1).strip()
        if "select" not in imports:
            new_imports = imports + ", select"
            content = content.replace(
                f"from sqlalchemy import {imports}",
                f"from sqlalchemy import {new_imports}",
            )

    return content


def convert_simple_query_first(line: str, indent: str = "\t") -> str:
    """
    Convert: db.query(Model).filter(...).first()
    To:      result = await db.execute(select(Model).where(...))
             item = result.scalar_one_or_none()
    """
    # Pattern: db.query(ModelName).filter(conditions).first()
    pattern = r"(\w+)\s*=\s*db\.query\((\w+)\)\.filter\(([^)]+(?:\([^)]*\))?[^)]*)\)\.first\(\)"
    match = re.search(pattern, line)

    if not match:
        return None

    var_name = match.group(1)
    model = match.group(2)
    conditions = match.group(3)

    # Convert .filter() conditions to .where()
    # This handles complex conditions with multiple filters
    return f"""{indent}result = await db.execute(select({model}).where({conditions}))
{indent}{var_name} = result.scalar_one_or_none()"""


def convert_simple_query_all(line: str, indent: str = "\t") -> str:
    """
    Convert: items = db.query(Model).filter(...).order_by(...).offset(skip).limit(limit).all()
    To:      result = await db.execute(select(Model).where(...).order_by(...).offset(skip).limit(limit))
             items = result.scalars().all()
    """
    # Pattern for query with all()
    pattern = r"(\w+)\s*=\s*db\.query\((\w+)\)\.filter\(([^)]+(?:\([^)]*\))?[^)]*)\)((?:\.\w+\([^)]*\))*)\.all\(\)"
    match = re.search(pattern, line)

    if not match:
        return None

    var_name = match.group(1)
    model = match.group(2)
    conditions = match.group(3)
    chain = match.group(4) or ""

    return f"""{indent}result = await db.execute(select({model}).where({conditions}){chain})
{indent}{var_name} = result.scalars().all()"""


def convert_query_chained(line: str, indent: str = "\t") -> tuple:
    """
    Convert multi-line query pattern:
    query = db.query(Model).filter(...)
    if condition:
        query = query.filter(...)
    items = query.order_by(...).all()

    Returns tuple of (query_line, is_query_start)
    """
    # Check if this is a query assignment
    query_start = (
        r"(\w+)\s*=\s*db\.query\((\w+)\)\.filter\(([^)]+(?:\([^)]*\))?[^)]*)\)"
    )
    match = re.search(query_start, line)

    if match:
        var_name = match.group(1)
        model = match.group(2)
        conditions = match.group(3)
        return (f"{indent}stmt = select({model}).where({conditions})", True)

    # Check if this is a query chain continuation
    query_chain = r"(\w+)\s*=\s*(\w+)\.filter\(([^)]+(?:\([^)]*\))?[^)]*)\)"
    match = re.search(query_chain, line)

    if match:
        var_name = match.group(1)
        stmt_name = match.group(2)
        conditions = match.group(3)
        return (f"{indent}{var_name} = {stmt_name}.where({conditions})", False)

    # Check if this is executing the query
    query_exec = r"(\w+)\s*=\s*(\w+)\.(order_by\([^)]+\))?(\.offset\([^)]+\))?(\.limit\([^)]+\))?\.all\(\)"
    match = re.search(query_exec, line)

    if match:
        var_name = match.group(1)
        stmt_name = match.group(2)
        chain_parts = [p for p in match.groups()[2:] if p]
        chain = "".join(chain_parts)
        return (
            f"""{indent}result = await db.execute({stmt_name}{chain})
{indent}{var_name} = result.scalars().all()""",
            False,
        )

    return (None, False)


def convert_file(filepath: Path) -> bool:
    """Convert a single file's queries to async"""
    try:
        content = filepath.read_text()
        original_content = content

        # Track changes
        changes = []

        # Add select import if needed
        if needs_select_import(content):
            content = add_select_import(content)
            changes.append("Added select import")

        lines = content.split("\n")
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            indent = len(line) - len(line.lstrip())
            indent_str = line[:indent] if indent > 0 else "\t"

            # Try to convert simple .first() pattern
            converted = convert_simple_query_first(line, indent_str)
            if converted:
                new_lines.append(converted)
                changes.append(f"Converted .first() query at line {i + 1}")
                i += 1
                continue

            # Try to convert simple .all() pattern
            converted = convert_simple_query_all(line, indent_str)
            if converted:
                new_lines.append(converted)
                changes.append(f"Converted .all() query at line {i + 1}")
                i += 1
                continue

            # Try to convert chained query pattern
            converted, is_start = convert_query_chained(line, indent_str)
            if converted:
                new_lines.append(converted)
                if is_start:
                    changes.append(f"Converted query start at line {i + 1}")
                else:
                    changes.append(f"Converted query chain at line {i + 1}")
                i += 1
                continue

            # No conversion needed, keep original line
            new_lines.append(line)
            i += 1

        # Join lines back together
        new_content = "\n".join(new_lines)

        # Only write if there were changes
        if new_content != original_content:
            filepath.write_text(new_content)
            print(f"✓ Converted {filepath.name}:")
            for change in changes:
                print(f"  - {change}")
            return True
        else:
            print(f"○ No changes needed in {filepath.name}")
            return False

    except Exception as e:
        print(f"✗ Error converting {filepath}: {e}")
        return False


def main():
    """Convert critical API files to async queries"""
    backend_dir = Path(__file__).parent
    api_dir = backend_dir / "app" / "api" / "v1"

    # Focus on the most critical files first
    critical_files = [
        "applications.py",
        "jobs.py",
        "dashboard.py",
        "recommendations.py",
    ]

    converted_count = 0

    print("=" * 60)
    print("Converting critical API files to async queries...")
    print("=" * 60)
    print()

    for filename in critical_files:
        filepath = api_dir / filename
        if filepath.exists():
            if convert_file(filepath):
                converted_count += 1
        else:
            print(f"✗ File not found: {filename}")

    print()
    print("=" * 60)
    print(f"Converted {converted_count} critical files")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the converted files")
    print("2. Test the endpoints with curl")
    print("3. Run the conversion on remaining files")


if __name__ == "__main__":
    main()
