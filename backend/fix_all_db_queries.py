#!/usr/bin/env python3
"""Fix ALL remaining db.query() calls in API files"""

import re
from pathlib import Path


def fix_file(filepath):
    """Fix db.query() patterns in a single file"""
    with open(filepath) as f:
        content = f.read()

    original_content = content
    changes = []

    # Pattern 1: db.query(Model).filter(...).first() -> await db.execute(select(Model).where(...)); result.scalar_one_or_none()
    pattern1 = r"(\w+)\s*=\s*db\.query\((\w+)\)\.filter\((.*?)\)\.first\(\)"

    def replace1(match):
        var_name = match.group(1)
        model = match.group(2)
        filter_cond = match.group(3)
        # Convert filter conditions to where conditions
        where_cond = filter_cond.replace("==", " == ")
        changes.append(f"  - {var_name}: db.query().filter().first() -> async")
        return f"{var_name}_result = await db.execute(select({model}).where({where_cond}))\n\t{var_name} = {var_name}_result.scalar_one_or_none()"

    content = re.sub(pattern1, replace1, content)

    # Pattern 2: db.query(Model).filter(...).all() -> await db.execute(select(Model).where(...)); result.scalars().all()
    pattern2 = r"(\w+)\s*=\s*db\.query\((\w+)\)\.filter\((.*?)\)\.all\(\)"

    def replace2(match):
        var_name = match.group(1)
        model = match.group(2)
        filter_cond = match.group(3)
        where_cond = filter_cond.replace("==", " == ")
        changes.append(f"  - {var_name}: db.query().filter().all() -> async")
        return f"{var_name}_result = await db.execute(select({model}).where({where_cond}))\n\t{var_name} = {var_name}_result.scalars().all()"

    content = re.sub(pattern2, replace2, content)

    # Pattern 3: db.query(Model).get(id) -> await db.execute(select(Model).where(Model.id == id)); result.scalar_one_or_none()
    pattern3 = r"(\w+)\s*=\s*db\.query\((\w+)\)\.get\((\w+)\)"

    def replace3(match):
        var_name = match.group(1)
        model = match.group(2)
        id_var = match.group(3)
        changes.append(f"  - {var_name}: db.query().get() -> async")
        return f"{var_name}_result = await db.execute(select({model}).where({model}.id == {id_var}))\n\t{var_name} = {var_name}_result.scalar_one_or_none()"

    content = re.sub(pattern3, replace3, content)

    # Pattern 4: Simple db.query(Model).all() -> await db.execute(select(Model)); result.scalars().all()
    pattern4 = r"(\w+)\s*=\s*db\.query\((\w+)\)\.all\(\)"

    def replace4(match):
        var_name = match.group(1)
        model = match.group(2)
        changes.append(f"  - {var_name}: db.query().all() -> async")
        return f"{var_name}_result = await db.execute(select({model}))\n\t{var_name} = {var_name}_result.scalars().all()"

    content = re.sub(pattern4, replace4, content)

    # Pattern 5: db.query(Model).filter(...).order_by(...).all()
    pattern5 = (
        r"(\w+)\s*=\s*db\.query\((\w+)\)\.filter\((.*?)\)\.order_by\((.*?)\)\.all\(\)"
    )

    def replace5(match):
        var_name = match.group(1)
        model = match.group(2)
        filter_cond = match.group(3)
        order = match.group(4)
        where_cond = filter_cond.replace("==", " == ")
        changes.append(f"  - {var_name}: db.query().filter().order_by().all() -> async")
        return f"{var_name}_result = await db.execute(select({model}).where({where_cond}).order_by({order}))\n\t{var_name} = {var_name}_result.scalars().all()"

    content = re.sub(pattern5, replace5, content)

    # Add select import if not present and we made changes
    if content != original_content:
        if (
            "from sqlalchemy import select" not in content
            and "from sqlalchemy import" in content
        ):
            # Add select to existing sqlalchemy imports
            content = re.sub(
                r"from sqlalchemy import (.*)",
                lambda m: f"from sqlalchemy import {m.group(1)}, select"
                if "select" not in m.group(1)
                else m.group(0),
                content,
                count=1,
            )
        elif (
            "from sqlalchemy import" not in content
            and "import sqlalchemy" not in content
        ):
            # Add new import at the top after other imports
            import_pos = content.find("from app.")
            if import_pos > 0:
                content = (
                    content[:import_pos]
                    + "from sqlalchemy import select\n"
                    + content[import_pos:]
                )

    if content != original_content:
        with open(filepath, "w") as f:
            f.write(content)
        return True, changes

    return False, []


def main():
    api_dir = Path(__file__).parent / "app" / "api" / "v1"
    files_fixed = 0
    total_changes = 0

    print("🔧 Fixing ALL db.query() calls in API files...\n")

    for py_file in sorted(api_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue

        fixed, changes = fix_file(py_file)
        if fixed:
            files_fixed += 1
            total_changes += len(changes)
            print(f"✅ Fixed {py_file.name}")
            for change in changes:
                print(change)
            print()

    print("\n📊 Summary:")
    print(f"   Files fixed: {files_fixed}")
    print(f"   Total changes: {total_changes}")
    print("\n✅ Done! Now fixing any remaining manual patterns...")


if __name__ == "__main__":
    main()
