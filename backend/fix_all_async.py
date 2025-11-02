#!/usr/bin/env python3
"""
Comprehensive script to convert all remaining synchronous SQLAlchemy queries to async.
"""

import re
from pathlib import Path


def add_select_import(content: str) -> str:
    """Add select import if needed"""
    if "from sqlalchemy import" in content and "select" not in content:
        # Add select to existing import
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
    elif "from sqlalchemy import" not in content and "import sqlalchemy" not in content:
        # Add new import after AsyncSession import
        if "from sqlalchemy.ext.asyncio import AsyncSession" in content:
            content = content.replace(
                "from sqlalchemy.ext.asyncio import AsyncSession",
                "from sqlalchemy.ext.asyncio import AsyncSession\nfrom sqlalchemy import select",
            )
    return content


def convert_query_filter_first(content: str) -> str:
    """Convert db.query(Model).filter(...).first() to async"""
    # Pattern for simple .first() queries
    pattern = r"(\s+)(\w+)\s*=\s*db\.query\((\w+)\)\.filter\(([^)]+(?:\([^)]*\))?[^)]*)\)\.first\(\)"

    def replacer(match):
        indent = match.group(1)
        var_name = match.group(2)
        model = match.group(3)
        conditions = match.group(4)
        return f"{indent}result = await db.execute(select({model}).where({conditions}))\n{indent}{var_name} = result.scalar_one_or_none()"

    return re.sub(pattern, replacer, content)


def convert_query_filter_all(content: str) -> str:
    """Convert db.query(Model).filter(...).all() to async"""
    # Pattern for .all() queries with various chaining
    pattern = r"(\s+)(\w+)\s*=\s*db\.query\((\w+)\)\.filter\(([^)]+(?:\([^)]*\))?[^)]*)\)((?:\.(?:order_by|offset|limit)\([^)]*\))*)\.all\(\)"

    def replacer(match):
        indent = match.group(1)
        var_name = match.group(2)
        model = match.group(3)
        conditions = match.group(4)
        chain = match.group(5) or ""
        return f"{indent}result = await db.execute(select({model}).where({conditions}){chain})\n{indent}{var_name} = result.scalars().all()"

    return re.sub(pattern, replacer, content)


def convert_query_update(content: str) -> str:
    """Convert db.query(Model).filter(...).update(...) to async"""
    # This is more complex - need to fetch, update, and save
    pattern = r"(\s+)db\.query\((\w+)\)\.filter\(([^)]+(?:\([^)]*\))?[^)]*)\)\.update\(([^)]+)\)"

    def replacer(match):
        indent = match.group(1)
        model = match.group(2)
        conditions = match.group(3)
        updates = match.group(4)
        return f"{indent}# Update operation - fetch and update\n{indent}result = await db.execute(select({model}).where({conditions}))\n{indent}items = result.scalars().all()\n{indent}for item in items:\n{indent}    for key, value in {updates}.items():\n{indent}        setattr(item, key, value)"

    return re.sub(pattern, replacer, content)


def convert_query_count(content: str) -> str:
    """Convert db.query(Model).filter(...).count() to async"""
    pattern = r"(\s+)(\w+)\s*=\s*db\.query\((\w+)\)\.filter\(([^)]+(?:\([^)]*\))?[^)]*)\)\.count\(\)"

    def replacer(match):
        indent = match.group(1)
        var_name = match.group(2)
        model = match.group(3)
        conditions = match.group(4)
        return f"{indent}result = await db.execute(select(func.count()).select_from({model}).where({conditions}))\n{indent}{var_name} = result.scalar() or 0"

    return re.sub(pattern, replacer, content)


def convert_simple_filter(content: str) -> str:
    """Convert .filter() to .where() in select statements"""
    # Replace .filter( with .where( in select statements
    content = re.sub(r"select\(([^)]+)\)\.filter\(", r"select(\1).where(", content)
    return content


def convert_db_operations(content: str) -> str:
    """Add await to db.commit() and db.refresh()"""
    # Add await to db.commit() if not already present
    content = re.sub(r"([^\w])db\.commit\(\)", r"\1await db.commit()", content)
    # Add await to db.refresh() if not already present
    content = re.sub(r"([^\w])db\.refresh\(", r"\1await db.refresh(", content)
    # Don't add await to db.delete() - it's not async
    return content


def add_func_import(content: str) -> str:
    """Add func import if count() is used"""
    if (
        "func.count()" in content
        and "func" not in content.split("from sqlalchemy import")[1].split("\n")[0]
        if "from sqlalchemy import" in content
        else True
    ):
        if "from sqlalchemy import" in content and "select" in content:
            content = content.replace(
                "from sqlalchemy import", "from sqlalchemy import func,"
            )
    return content


def fix_file(filepath: Path) -> tuple[bool, list[str]]:
    """Fix a single file"""
    try:
        content = filepath.read_text()
        original_content = content
        changes = []

        # Skip if already fully converted
        if (
            "db.query(" not in content
            and "db.commit()" not in content
            and "db.refresh(" not in content
        ):
            return False, []

        # Add imports
        if "db.query(" in content or "select(" in content:
            old_content = content
            content = add_select_import(content)
            if content != old_content:
                changes.append("Added select import")

        # Convert queries
        old_content = content
        content = convert_query_filter_first(content)
        content = convert_query_filter_all(content)
        content = convert_query_update(content)
        content = convert_query_count(content)
        content = convert_simple_filter(content)
        if content != old_content:
            changes.append("Converted db.query() calls")

        # Convert db operations
        old_content = content
        content = convert_db_operations(content)
        if content != old_content:
            changes.append("Added await to db operations")

        # Add func import if needed
        old_content = content
        content = add_func_import(content)
        if content != old_content:
            changes.append("Added func import")

        # Write if changed
        if content != original_content:
            filepath.write_text(content)
            return True, changes

        return False, []

    except Exception as e:
        print(f"✗ Error fixing {filepath}: {e}")
        return False, []


def main():
    """Fix all API endpoint files"""
    backend_dir = Path(__file__).parent
    api_dir = backend_dir / "app" / "api" / "v1"

    # Get all Python files
    files = sorted(api_dir.glob("*.py"))

    print("=" * 70)
    print("Converting all remaining endpoints to async...")
    print("=" * 70)
    print()

    fixed_count = 0
    skipped_files = []

    for filepath in files:
        if filepath.name in ["__init__.py"]:
            continue

        changed, changes = fix_file(filepath)

        if changed:
            print(f"✓ Fixed {filepath.name}:")
            for change in changes:
                print(f"  - {change}")
            fixed_count += 1
        else:
            if "db.query(" in filepath.read_text():
                skipped_files.append(filepath.name)

    print()
    print("=" * 70)
    print(f"Fixed {fixed_count} files")
    print("=" * 70)

    if skipped_files:
        print()
        print("Files that still need manual review:")
        for fname in skipped_files:
            print(f"  - {fname}")

    print()
    print("Next: Restart the server and test endpoints")


if __name__ == "__main__":
    main()
