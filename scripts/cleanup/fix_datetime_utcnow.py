#!/usr/bin/env python3
"""
Script to replace deprecated datetime.utcnow() with datetime.now(timezone.utc)
"""

import re
import sys
from pathlib import Path


def fix_datetime_imports(content: str) -> str:
	"""Add timezone import if needed and datetime import exists."""
	# Check if datetime is imported
	has_datetime_import = bool(re.search(r"from datetime import.*\bdatetime\b", content))

	if not has_datetime_import:
		return content

	# Check if timezone is already imported
	has_timezone = bool(re.search(r"from datetime import.*\btimezone\b", content))

	if has_timezone:
		return content

	# Add timezone to existing datetime imports
	def add_timezone(match):
		import_line = match.group(0)
		# Check if it's already there
		if "timezone" in import_line:
			return import_line

		# Add timezone to the import
		# Handle various formats
		if import_line.endswith(")"):
			# Multi-line import
			return import_line[:-1] + ", timezone)"
		else:
			# Single line import
			return import_line + ", timezone"

	content = re.sub(r"from datetime import [^;\n]+", add_timezone, content, count=1)

	return content


def fix_utcnow_calls(content: str) -> str:
	"""Replace datetime.utcnow() with datetime.now(timezone.utc)."""
	# Replace datetime.utcnow() with datetime.now(timezone.utc)
	content = re.sub(r"\bdatetime\.utcnow\(\)", "datetime.now(timezone.utc)", content)
	return content


def process_file(file_path: Path) -> bool:
	"""Process a single file."""
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			original_content = f.read()

		# Skip if no utcnow
		if "datetime.utcnow()" not in original_content:
			return False

		# Fix imports first
		content = fix_datetime_imports(original_content)

		# Fix utcnow calls
		content = fix_utcnow_calls(content)

		# Only write if changed
		if content != original_content:
			with open(file_path, "w", encoding="utf-8") as f:
				f.write(content)
			print(f"✓ Fixed: {file_path}")
			return True

		return False

	except Exception as e:
		print(f"✗ Error processing {file_path}: {e}", file=sys.stderr)
		return False


def main():
	"""Main function."""
	backend_path = Path(__file__).parent.parent / "backend" / "app"

	if not backend_path.exists():
		print(f"Error: Backend path not found: {backend_path}", file=sys.stderr)
		sys.exit(1)

	# Find all Python files
	python_files = list(backend_path.rglob("*.py"))

	print(f"Found {len(python_files)} Python files")
	print("Fixing datetime.utcnow() calls...\n")

	fixed_count = 0
	for file_path in python_files:
		if process_file(file_path):
			fixed_count += 1

	print(f"\n✓ Fixed {fixed_count} files")


if __name__ == "__main__":
	main()
