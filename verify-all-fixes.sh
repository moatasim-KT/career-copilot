#!/bin/bash
# =============================================================================
# ⚠️  DEPRECATED: This script is deprecated
# =============================================================================
# Please use the canonical verification script instead:
#   ./scripts/verify/frontend.sh --structural
#
# This shim redirects to the new location for backward compatibility.
# Will be removed in 6 months (April 2026).
# =============================================================================

echo "================================"
echo "⚠️  DEPRECATION WARNING"
echo "================================"
echo ""
echo "This script (verify-all-fixes.sh) is DEPRECATED."
echo ""
echo "Please use the canonical script instead:"
echo "  ./scripts/verify/frontend.sh --structural"
echo ""
echo "The canonical script provides:"
echo "  ✅ Unified verification (quick, structural, full modes)"
echo "  ✅ Better error reporting"
echo "  ✅ Consistent output formatting"
echo ""
echo "Redirecting in 2 seconds..."
echo ""

sleep 2

# Call canonical script
exec ./scripts/verify/frontend.sh --structural

