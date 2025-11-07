#!/usr/bin/env python3
"""
Script to replace console.log statements with logger calls in TypeScript/JavaScript files
"""

import re
import sys
from pathlib import Path
from typing import Tuple


def add_logger_import(content: str) -> str:
	"""Add logger import if console.log is being replaced."""
	# Check if logger is already imported
	if (
		"from '@/lib/logger'" in content
		or 'from "../lib/logger"' in content
		or 'from "../../lib/logger"' in content
		or 'from "../../../lib/logger"' in content
	):
		return content

	# Find the first import statement
	import_match = re.search(r"^import\s+", content, re.MULTILINE)

	if import_match:
		# Add logger import after the first import
		lines = content.split("\n")
		for i, line in enumerate(lines):
			if line.strip().startswith("import "):
				# Insert after this import
				lines.insert(i + 1, "import { logger } from '@/lib/logger';")
				return "\n".join(lines)

	# If no imports found, add at the beginning (after 'use client' if present)
	lines = content.split("\n")
	for i, line in enumerate(lines):
		if "'use client'" in line or '"use client"' in line:
			lines.insert(i + 1, "\nimport { logger } from '@/lib/logger';")
			return "\n".join(lines)

	# Add at the very beginning
	return "import { logger } from '@/lib/logger';\n\n" + content


def replace_console_logs(content: str) -> Tuple[str, int]:
	"""Replace console.log statements with logger calls."""
	replacements = 0

	# Replace console.log
	new_content, count = re.subn(r"\bconsole\.log\(", "logger.log(", content)
	replacements += count

	# Replace console.error (but keep it as logger.error)
	new_content, count = re.subn(r"\bconsole\.error\(", "logger.error(", new_content)
	replacements += count

	# Replace console.warn
	new_content, count = re.subn(r"\bconsole\.warn\(", "logger.warn(", new_content)
	replacements += count

	# Replace console.info
	new_content, count = re.subn(r"\bconsole\.info\(", "logger.info(", new_content)
	replacements += count

	# Replace console.debug
	new_content, count = re.subn(r"\bconsole\.debug\(", "logger.debug(", new_content)
	replacements += count

	return new_content, replacements


def process_file(file_path: Path) -> Tuple[bool, int]:
	"""Process a single file."""
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			original_content = f.read()

		# Skip if no console statements
		if not re.search(r"\bconsole\.(log|error|warn|info|debug)\(", original_content):
			return False, 0

		# Replace console logs
		content, replacements = replace_console_logs(original_content)

		# Add logger import if we made replacements
		if replacements > 0:
			content = add_logger_import(content)

		# Only write if changed
		if content != original_content:
			with open(file_path, "w", encoding="utf-8") as f:
				f.write(content)
			print(f"✓ Fixed: {file_path.relative_to(file_path.parent.parent.parent)} ({replacements} replacements)")
			return True, replacements

		return False, 0

	except Exception as e:
		print(f"✗ Error processing {file_path}: {e}", file=sys.stderr)
		return False, 0


def main():
	"""Main function."""
	frontend_path = Path(__file__).parent.parent / "frontend" / "src"

	if not frontend_path.exists():
		print(f"Error: Frontend path not found: {frontend_path}", file=sys.stderr)
		sys.exit(1)

	# Find all TypeScript/JavaScript files
	ts_files = list(frontend_path.rglob("*.ts"))
	tsx_files = list(frontend_path.rglob("*.tsx"))
	js_files = list(frontend_path.rglob("*.js"))
	jsx_files = list(frontend_path.rglob("*.jsx"))

	all_files = ts_files + tsx_files + js_files + jsx_files

	print(f"Found {len(all_files)} TypeScript/JavaScript files")
	print("Replacing console statements with logger...\n")

	fixed_count = 0
	total_replacements = 0

	for file_path in all_files:
		fixed, replacements = process_file(file_path)
		if fixed:
			fixed_count += 1
			total_replacements += replacements

	print(f"\n✓ Fixed {fixed_count} files ({total_replacements} total replacements)")


if __name__ == "__main__":
	main()
