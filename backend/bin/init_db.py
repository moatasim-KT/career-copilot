"""
⚠️  DEPRECATED: This script is deprecated.

Please use the canonical database initialization script instead:
    python scripts/database/initialize_database.py

This shim redirects to the new location for backward compatibility.
Will be removed in 6 months (April 2026).
"""

import subprocess
import sys
from pathlib import Path

print("=" * 70)
print("⚠️  DEPRECATION WARNING")
print("=" * 70)
print("")
print("This script (backend/scripts/init_database.py) is DEPRECATED.")
print("")
print("Please use the canonical script instead:")
print("  python scripts/database/initialize_database.py")
print("")
print("The canonical script provides:")
print("  ✅ Async database operations")
print("  ✅ CLI arguments (--no-seed, --force-reseed, --tables-only)")
print("  ✅ Health validation")
print("  ✅ Comprehensive error handling")
print("")
print("Redirecting to canonical script in 3 seconds...")
print("=" * 70)
print("")

import time

time.sleep(3)

# Get the project root (two levels up from this script)
project_root = Path(__file__).resolve().parent.parent.parent
canonical_script = project_root / "scripts" / "database" / "initialize_database.py"

# Validate that the canonical script exists
if not canonical_script.exists():
    print(f"Error: Canonical script not found at {canonical_script}")
    sys.exit(1)

# Forward all arguments to the canonical script using subprocess.run for security
try:
    result = subprocess.run(
        [sys.executable, str(canonical_script), *sys.argv[1:]],
        check=False,
    )
    sys.exit(result.returncode)
except Exception as e:
    print(f"Error executing canonical script: {e}")
    sys.exit(1)
