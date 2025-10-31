#!/usr/bin/env python3
"""
Comprehensive Security Audit Script

Performs a comprehensive security audit of the Career Copilot repository, checking for:
- Exposed secrets and credentials
- Python dependency vulnerabilities
- Code security issues (via Bandit)
- .gitignore configuration
- Environment file handling
- Hardcoded credentials

Usage:
    # Run full audit
    python scripts/security/security_audit.py

    # Run with verbose output
    python scripts/security/security_audit.py -v

    # Skip specific checks
    python scripts/security/security_audit.py --skip-bandit --skip-safety

    # Fail on any issue (for CI/CD)
    python scripts/security/security_audit.py --strict

    # Run only specific checks
    python scripts/security/security_audit.py --only-secrets --only-gitignore

Exit Codes:
    0: All security checks passed
    1: One or more security issues found
    2: Error running audit checks

Examples:
    # Quick scan without dependency checks
    python scripts/security/security_audit.py --skip-safety --skip-bandit

    # CI/CD mode (strict)
    python scripts/security/security_audit.py --strict -v

    # Just check for secrets and environment files
    python scripts/security/security_audit.py --only-secrets --only-env
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str, verbose: bool = False) -> bool:
	"""
	Run command and return success status.

	Args:
		cmd: Command and arguments to execute
		description: Human-readable description of the check
		verbose: Whether to show detailed output

	Returns:
		True if command succeeded, False otherwise
	"""
	print(f"\n{'=' * 60}")
	print(f"🔍 {description}")
	print(f"{'=' * 60}")

	try:
		result = subprocess.run(cmd, capture_output=True, text=True, check=False)
		if verbose or result.returncode != 0:
			print(result.stdout)
			if result.stderr:
				print(result.stderr)
		elif result.returncode == 0:
			print("✅ Check passed")
		return result.returncode == 0
	except Exception as e:
		print(f"❌ Error: {e}")
		return False


def parse_arguments() -> argparse.Namespace:
	"""Parse command line arguments."""
	parser = argparse.ArgumentParser(
		description="Comprehensive security audit for Career Copilot repository", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__
	)

	parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output for all checks")

	parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any issues found (for CI/CD)")

	# Skip options
	skip_group = parser.add_argument_group("Skip Checks")
	skip_group.add_argument("--skip-secrets", action="store_true", help="Skip exposed secrets check")
	skip_group.add_argument("--skip-safety", action="store_true", help="Skip Python dependency vulnerability check (requires safety)")
	skip_group.add_argument("--skip-bandit", action="store_true", help="Skip Bandit static security analysis (requires bandit)")
	skip_group.add_argument("--skip-gitignore", action="store_true", help="Skip .gitignore validation")
	skip_group.add_argument("--skip-env", action="store_true", help="Skip environment file checks")
	skip_group.add_argument("--skip-hardcoded", action="store_true", help="Skip hardcoded credentials scan")

	# Only options
	only_group = parser.add_argument_group("Run Only Specific Checks")
	only_group.add_argument("--only-secrets", action="store_true", help="Run only secrets check")
	only_group.add_argument("--only-safety", action="store_true", help="Run only dependency vulnerability check")
	only_group.add_argument("--only-bandit", action="store_true", help="Run only Bandit analysis")
	only_group.add_argument("--only-gitignore", action="store_true", help="Run only .gitignore validation")
	only_group.add_argument("--only-env", action="store_true", help="Run only environment file checks")
	only_group.add_argument("--only-hardcoded", action="store_true", help="Run only hardcoded credentials scan")

	return parser.parse_args()


def should_run_check(check_name: str, args: argparse.Namespace) -> bool:
	"""Determine if a specific check should run based on args."""
	# Check if any --only flags are set
	only_flags = [args.only_secrets, args.only_safety, args.only_bandit, args.only_gitignore, args.only_env, args.only_hardcoded]
	only_mode = any(only_flags)

	# Map check names to their flags
	check_map = {
		"secrets": (args.skip_secrets, args.only_secrets),
		"python_deps": (args.skip_safety, args.only_safety),
		"bandit": (args.skip_bandit, args.only_bandit),
		"gitignore": (args.skip_gitignore, args.only_gitignore),
		"env_files": (args.skip_env, args.only_env),
		"hardcoded": (args.skip_hardcoded, args.only_hardcoded),
	}

	if check_name not in check_map:
		return True

	skip_flag, only_flag = check_map[check_name]

	# If in only mode, run only if this check's only flag is set
	if only_mode:
		return only_flag

	# Otherwise, run unless skip flag is set
	return not skip_flag


def main():
	"""Run security audit"""
	args = parse_arguments()

	print("🔐 Career Copilot - Security Audit")
	print("=" * 60)

	repo_root = Path(__file__).parent.parent.parent
	results = {}

	# 1. Check for secrets
	if should_run_check("secrets", args):
		print("\n1️⃣  Checking for exposed secrets...")
		results["secrets"] = run_command(
			[sys.executable, str(repo_root / "scripts/security/check_secrets.py")], "Scanning for exposed secrets", args.verbose
		)

	# 2. Python dependency vulnerabilities
	if should_run_check("python_deps", args):
		print("\n2️⃣  Checking Python dependencies...")
		results["python_deps"] = run_command(["safety", "check", "--json"], "Scanning Python dependencies for vulnerabilities", args.verbose)

	# 3. Bandit security linter
	if should_run_check("bandit", args):
		print("\n3️⃣  Running Bandit security linter...")
		results["bandit"] = run_command(
			["bandit", "-r", str(repo_root / "backend/app"), "-f", "txt"], "Static security analysis with Bandit", args.verbose
		)

	# 4. Check .gitignore
	if should_run_check("gitignore", args):
		print("\n4️⃣  Validating .gitignore...")
		gitignore_path = repo_root / ".gitignore"
		required_patterns = [".env", "*.db", "secrets/", "*.log"]
		missing = []

		if gitignore_path.exists():
			content = gitignore_path.read_text()
			for pattern in required_patterns:
				if pattern not in content:
					missing.append(pattern)

			if missing:
				print(f"⚠️  Missing patterns in .gitignore: {', '.join(missing)}")
				results["gitignore"] = False
			else:
				print("✅ .gitignore properly configured")
				results["gitignore"] = True
		else:
			print("❌ .gitignore not found")
			results["gitignore"] = False

	# 5. Check environment files
	if should_run_check("env_files", args):
		print("\n5️⃣  Checking environment files...")
		env_file = repo_root / "backend/.env"
		env_example = repo_root / "backend/.env.example"

		if env_file.exists():
			print("⚠️  .env file exists (should be gitignored)")
			# Check if it's in git
			result = subprocess.run(["git", "ls-files", str(env_file)], capture_output=True, text=True, cwd=repo_root)
			if result.stdout.strip():
				print("❌ CRITICAL: .env file is tracked by git!")
				results["env_files"] = False
			else:
				print("✅ .env file is properly gitignored")
				results["env_files"] = True
		else:
			print("✅ No .env file in repository")
			results["env_files"] = True

		if not env_example.exists():
			print("⚠️  .env.example not found")

	# 6. Check for hardcoded secrets
	if should_run_check("hardcoded", args):
		print("\n6️⃣  Checking for hardcoded credentials...")
		dangerous_patterns = [
			"password = ",
			"api_key = ",
			"secret = ",
			"token = ",
		]

		found_issues = []
		for py_file in (repo_root / "backend/app").rglob("*.py"):
			try:
				content = py_file.read_text()
				for pattern in dangerous_patterns:
					if pattern in content.lower():
						found_issues.append(f"{py_file.name}: {pattern}")
			except:
				pass

		if found_issues:
			print(f"⚠️  Found {len(found_issues)} potential hardcoded credentials")
			for issue in found_issues[:5]:  # Show first 5
				print(f"   - {issue}")
			results["hardcoded"] = False
		else:
			print("✅ No obvious hardcoded credentials found")
			results["hardcoded"] = True

	# Summary
	print("\n" + "=" * 60)
	print("📊 SECURITY AUDIT SUMMARY")
	print("=" * 60)

	passed = sum(1 for v in results.values() if v)
	total = len(results)

	for check, status in results.items():
		icon = "✅" if status else "❌"
		print(f"{icon} {check.replace('_', ' ').title()}")

	print(f"\nScore: {passed}/{total} checks passed")

	if passed == total:
		print("\n🎉 All security checks passed!")
		return 0
	else:
		print(f"\n⚠️  {total - passed} security issues found")
		print("\nRecommended actions:")
		print("1. Review and fix identified issues")
		print("2. Rotate any exposed credentials")
		print("3. Update dependencies with vulnerabilities")
		print("4. Run audit again after fixes")

		if args.strict:
			return 1
		return 0 if args.verbose else 1


if __name__ == "__main__":
	sys.exit(main())
