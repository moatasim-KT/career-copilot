#!/bin/bash
# =============================================================================
# ⚠️  DEPRECATED: This script is deprecated
# =============================================================================
# Please use the canonical verification script instead:
#   ./scripts/verify/frontend.sh --quick
#
# This shim redirects to the new location for backward compatibility.
# Will be removed in 6 months (April 2026).
# =============================================================================

echo "=================================="
echo "⚠️  DEPRECATION WARNING"
echo "=================================="
echo ""
echo "This script (frontend/verify-fixes.sh) is DEPRECATED."
echo ""
echo "Please use the canonical script instead:"
echo "  ./scripts/verify/frontend.sh --quick"
echo ""
echo "The canonical script provides:"
echo "  ✅ Unified verification (quick, structural, full modes)"
echo "  ✅ Better error reporting"
echo "  ✅ Consistent output formatting"
echo ""
echo "Redirecting in 2 seconds..."
echo ""

sleep 2

# Get to project root and call canonical script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec "$PROJECT_ROOT/scripts/verify/frontend.sh" --quick

