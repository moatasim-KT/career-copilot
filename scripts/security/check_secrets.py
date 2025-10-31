#!/usr/bin/env python3
"""
Secret Scanner for Career Copilot Repository

This script scans the repository for potentially exposed secrets, API keys,
passwords, and other sensitive information.

Features:
- Pattern matching for common secret types (AWS keys, API keys, passwords, etc.)
- Configurable ignore patterns
- Line-by-line reporting
- Exit code 1 if secrets found (for CI/CD integration)

Usage:
    python check_secrets.py [options]

    Options:
        -h, --help          Show this help message
        -v, --verbose       Show verbose output
        -q, --quiet         Only show summary
        --path PATH         Scan specific path (default: repository root)
        --fail-on-found     Exit with code 1 if secrets found (for CI/CD)

Examples:
    # Scan entire repository
    python check_secrets.py

    # Scan specific directory
    python check_secrets.py --path /path/to/dir

    # Use in CI/CD (fails if secrets found)
    python check_secrets.py --fail-on-found

Exit Codes:
    0 - No secrets found
    1 - Secrets found (when --fail-on-found is used)
    2 - Error during execution
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# Patterns to detect secrets
# deepcode ignore NoHardcodedPasswords: This is a security scanner - regex patterns for detecting secrets
SECRET_PATTERNS = {
	"AWS Access Key": r"AKIA[0-9A-Z]{16}",
	"Generic API Key": r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}',
	"Generic Secret": r'secret["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}',
	"Password": r'password["\']?\s*[:=]\s*["\']?[^\s]{8,}',
	"Private Key": r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----",
	"JWT Token": r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
	"OpenAI Key": r"sk-[a-zA-Z0-9]{48}",
}

# Files to ignore
IGNORE_PATTERNS = [
	r"\.git/",
	r"\.env\.example",
	r"\.env\.template",
	r"node_modules/",
	r"venv/",
	r"__pycache__/",
	r"\.pyc$",
	r"\.log$",
	r"\.db$",
	r"check_secrets\.py$",
]


def should_ignore(filepath: str) -> bool:
	"""Check if file should be ignored"""
	for pattern in IGNORE_PATTERNS:
		if re.search(pattern, filepath):
			return True
	return False


def scan_file(filepath: Path, verbose: bool = False) -> list:
	"""
	Scan a file for potential secrets.

	Args:
		filepath: Path to file to scan
		verbose: Whether to print verbose output

	Returns:
		List of findings with file, line, type, and matched text
	"""
	findings = []

	try:
		# Path validation was performed in main() via is_relative_to() check
		# deepcode ignore PT: Path is validated in main() before calling scan_file
		with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
			content = f.read()

		for secret_type, pattern in SECRET_PATTERNS.items():
			matches = re.finditer(pattern, content, re.IGNORECASE)
			for match in matches:
				# Get line number
				line_num = content[: match.start()].count("\n") + 1
				findings.append(
					{
						"file": str(filepath),
						"line": line_num,
						"type": secret_type,
						"match": match.group()[:50] + "..." if len(match.group()) > 50 else match.group(),
					}
				)

				if verbose:
					print(f"  Found {secret_type} at line {line_num}")
	except Exception as e:
		if verbose:
			print(f"  Error scanning {filepath}: {e}")

	return findings


def parse_arguments() -> argparse.Namespace:
	"""Parse command line arguments."""
	parser = argparse.ArgumentParser(
		description="Scan repository for exposed secrets and sensitive information",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=__doc__,
	)

	parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output during scanning")

	parser.add_argument("-q", "--quiet", action="store_true", help="Only show summary (no individual findings)")

	parser.add_argument("--path", type=Path, default=None, help="Specific path to scan (default: repository root)")

	parser.add_argument("--fail-on-found", action="store_true", help="Exit with code 1 if secrets are found (useful for CI/CD)")

	return parser.parse_args()


def main():
	"""Main function"""
	args = parse_arguments()

	if not args.quiet:
		print("🔍 Scanning for exposed secrets...")
		print("=" * 60)

	# Determine scan root
	if args.path:
		# Security: Validate scan path to prevent path traversal (CWE-22)
		repo_root = Path(args.path).resolve()
		
		# Ensure the path is within the project directory
		project_root = Path(__file__).parent.parent.parent.resolve()
		
		try:
			# Check if scan path is within project boundaries
			if not repo_root.is_relative_to(project_root):
				print(f"❌ Error: Scan path must be within project directory: {project_root}")
				print(f"   Attempted path: {repo_root}")
				sys.exit(1)
		except (ValueError, OSError) as e:
			print(f"❌ Error: Invalid scan path: {e}")
			sys.exit(1)
	else:
		repo_root = Path(__file__).parent.parent.parent

	if args.verbose:
		print(f"Scanning directory: {repo_root}")

	all_findings = []
	files_scanned = 0

	# Scan all files
	for filepath in repo_root.rglob("*"):
		if filepath.is_file() and not should_ignore(str(filepath.relative_to(repo_root))):
			if args.verbose:
				print(f"Scanning: {filepath.relative_to(repo_root)}")

			findings = scan_file(filepath, args.verbose)
			all_findings.extend(findings)
			files_scanned += 1

	# Report findings
	if not args.quiet:
		print(f"\nScanned {files_scanned} files")

	if all_findings:
		if not args.quiet:
			print(f"\n⚠️  Found {len(all_findings)} potential secrets:\n")
			for finding in all_findings:
				print(f"  {finding['type']}")
				print(f"    File: {finding['file']}")
				print(f"    Line: {finding['line']}")
				print(f"    Match: {finding['match']}")
				print()

			print("=" * 60)
			print("❌ SECURITY ISSUE: Secrets detected in repository")
			print("\nRecommended actions:")
			print("1. Remove secrets from files")
			print("2. Use environment variables")
			print("3. Add files to .gitignore")
			print("4. Rotate exposed credentials")
			print("5. Use git-secrets or similar tools")

		sys.exit(1 if args.fail_on_found else 0)
	else:
		if not args.quiet:
			print("\n✅ No secrets detected in repository")
			print("=" * 60)
		sys.exit(0)


if __name__ == "__main__":
	main()
