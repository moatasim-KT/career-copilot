#!/usr/bin/env python3
"""
Script to replace console.* calls with proper logger usage in TypeScript/TSX files.
"""

import os
import re
from pathlib import Path

# Files to process
SRC_DIR = Path("src")

# Patterns to replace
CONSOLE_PATTERNS = {
	r"console\.log\(": "logger.info(",
	r"console\.info\(": "logger.info(",
	r"console\.warn\(": "logger.warn(",
	r"console\.error\(": "logger.error(",
	r"console\.debug\(": "logger.debug(",
}

# Import statement to add if not present
LOGGER_IMPORT = "import { logger } from '@/lib/logger';"


def has_logger_import(content: str) -> bool:
	"""Check if file already imports logger"""
	return "from '@/lib/logger'" in content or 'from "@/lib/logger"' in content


def add_logger_import(content: str) -> str:
	"""Add logger import after React import or at the top"""
	lines = content.split("\n")

	# Find where to insert (after 'use client' or first import)
	insert_idx = 0
	for i, line in enumerate(lines):
		if "'use client'" in line or '"use client"' in line:
			insert_idx = i + 1
			break
		if line.startswith("import ") and insert_idx == 0:
			insert_idx = i
			break

	# Insert logger import
	if insert_idx > 0:
		# Add after existing imports
		while insert_idx < len(lines) and (lines[insert_idx].startswith("import ") or lines[insert_idx].strip() == ""):
			insert_idx += 1
		lines.insert(insert_idx, LOGGER_IMPORT)
		lines.insert(insert_idx + 1, "")
	else:
		lines.insert(0, LOGGER_IMPORT)
		lines.insert(1, "")

	return "\n".join(lines)


def replace_console_calls(content: str) -> tuple[str, int]:
	"""Replace all console.* calls with logger calls"""
	replacements = 0
	new_content = content

	for pattern, replacement in CONSOLE_PATTERNS.items():
		new_content, count = re.subn(pattern, replacement, new_content)
		replacements += count

	return new_content, replacements


def process_file(filepath: Path) -> tuple[bool, int]:
	"""Process a single file"""
	try:
		with open(filepath, "r", encoding="utf-8") as f:
			content = f.read()

		# Skip if no console statements
		if not re.search(r"console\.(log|info|warn|error|debug)\(", content):
			return False, 0

		# Replace console calls
		new_content, replacements = replace_console_calls(content)

		if replacements > 0:
			# Add logger import if needed
			if not has_logger_import(new_content):
				new_content = add_logger_import(new_content)

			# Write back
			with open(filepath, "w", encoding="utf-8") as f:
				f.write(new_content)

			return True, replacements

		return False, 0

	except Exception as e:
		print(f"❌ Error processing {filepath}: {e}")
		return False, 0


def main():
	"""Process all TypeScript/TSX files"""
	print("🔍 Scanning for console.* calls in frontend/src...")

	total_files = 0
	total_replacements = 0
	modified_files = []

	# Find all .ts and .tsx files
	for ext in ["**/*.ts", "**/*.tsx"]:
		for filepath in SRC_DIR.glob(ext):
			# Skip test files and stories
			if ".test." in str(filepath) or ".spec." in str(filepath) or ".stories." in str(filepath):
				continue

			modified, replacements = process_file(filepath)
			if modified:
				total_files += 1
				total_replacements += replacements
				modified_files.append((filepath, replacements))
				print(f"✅ {filepath.relative_to(SRC_DIR)}: {replacements} replacements")

	print(f"\n📊 Summary:")
	print(f"   Files modified: {total_files}")
	print(f"   Total replacements: {total_replacements}")

	if total_files > 0:
		print(f"\n⚠️  Please review the changes and run: npm run lint -- --fix")
		print(f"   to fix any formatting issues.")


if __name__ == "__main__":
	main()
