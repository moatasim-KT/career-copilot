#!/bin/bash
# =============================================================================
# Canonical Frontend Verification Script
# =============================================================================
# This script provides comprehensive frontend quality checks in different modes
#
# Usage:
#   ./frontend.sh --quick      # Fast checks (TS errors, lint config)
#   ./frontend.sh --structural # File structure and code pattern checks
#   ./frontend.sh --full       # All checks + run linter/tests
#   ./frontend.sh              # Default: quick + structural
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
QUICK=false
STRUCTURAL=false
FULL=false

if [ $# -eq 0 ]; then
    # Default: quick + structural
    QUICK=true
    STRUCTURAL=true
else
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                QUICK=true
                shift
                ;;
            --structural)
                STRUCTURAL=true
                shift
                ;;
            --full)
                FULL=true
                QUICK=true
                STRUCTURAL=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--quick] [--structural] [--full]"
                exit 1
                ;;
        esac
    done
fi

# Get to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

cd "$FRONTEND_DIR"

echo -e "${BLUE}=================================="
echo "Frontend Verification"
echo -e "==================================${NC}"
echo ""

ERRORS=0

# =============================================================================
# Quick Checks (Compiler, Linter Config, Deprecations)
# =============================================================================

if [ "$QUICK" = true ]; then
    echo -e "${YELLOW}Running Quick Checks...${NC}"
    echo ""
    
    # 1. TypeScript Compilation Check
    echo "1. Checking TypeScript compilation..."
    TS_ERRORS=$(npx tsc --noEmit 2>&1 | grep "error TS" | wc -l | xargs)
    if [ "$TS_ERRORS" -eq 0 ]; then
        echo -e "   ${GREEN}✓${NC} No TypeScript errors ($TS_ERRORS errors)"
    else
        echo -e "   ${RED}✗${NC} TypeScript errors found: $TS_ERRORS"
        ERRORS=$((ERRORS + 1))
    fi
    echo ""
    
    # 2. Module Exports Check
    echo "2. Checking module exports..."
    EXPORT_FILES=(
        "src/lib/api/index.ts"
        "src/lib/websocket/index.ts"
        "src/lib/utils/index.ts"
        "src/components/ui/index.ts"
        "src/components/index.ts"
    )
    
    for file in "${EXPORT_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo -e "   ${GREEN}✓${NC} $file"
        else
            echo -e "   ${YELLOW}⚠${NC}  $file (not found)"
        fi
    done
    echo ""
    
    # 3. MSW Import Deprecation Check
    echo "3. Checking for deprecated MSW imports..."
    if grep -r "from 'msw/rest'" src/ 2>/dev/null; then
        echo -e "   ${RED}✗${NC} Found deprecated msw/rest imports"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "   ${GREEN}✓${NC} No deprecated msw/rest imports"
    fi
    echo ""
    
    # 4. ESLint Configuration Check
    echo "4. Checking ESLint configuration..."
    if [ -f "eslint.config.mjs" ]; then
        echo -e "   ${GREEN}✓${NC} ESLint config exists"
    else
        echo -e "   ${RED}✗${NC} ESLint config missing"
        ERRORS=$((ERRORS + 1))
    fi
    echo ""
fi

# =============================================================================
# Structural Checks (Files, Patterns, Code Quality)
# =============================================================================

if [ "$STRUCTURAL" = true ]; then
    echo -e "${YELLOW}Running Structural Checks...${NC}"
    echo ""
    
    # 1. Required Files Check
    echo "1. Checking required files..."
    REQUIRED_FILES=(
        "src/components/ErrorBoundary.tsx"
        "src/lib/utils/sanitize.ts"
        "src/lib/types/errors.ts"
        "README.md"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo -e "   ${GREEN}✓${NC} $file exists"
        else
            echo -e "   ${RED}✗${NC} $file missing"
            ERRORS=$((ERRORS + 1))
        fi
    done
    echo ""
    
    # 2. Deleted Files Check
    echo "2. Checking deleted files..."
    DELETED_FILES=(
        "src/components/ui/ContentGeneration.tsx"
        "src/components/ui/InterviewPractice.tsx"
    )
    
    for file in "${DELETED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "   ${GREEN}✓${NC} $file removed"
        else
            echo -e "   ${RED}✗${NC} $file still exists (should be deleted)"
            ERRORS=$((ERRORS + 1))
        fi
    done
    echo ""
    
    # 3. React.memo Usage Check
    echo "3. Checking React.memo usage..."
    
    if grep -q "memo(Button)" src/components/ui/Button.tsx 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Button.tsx uses React.memo"
    else
        echo -e "   ${YELLOW}⚠${NC}  Button.tsx missing React.memo"
    fi
    
    if grep -q "memo(function Card" src/components/ui/Card.tsx 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Card.tsx uses React.memo"
    else
        echo -e "   ${YELLOW}⚠${NC}  Card.tsx missing React.memo"
    fi
    echo ""
    
    # 4. Token Validation Check
    echo "4. Checking token expiry validation..."
    if grep -q "auth_token_expiry" src/components/auth/withAuth.tsx 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} withAuth.tsx has token expiry validation"
    else
        echo -e "   ${YELLOW}⚠${NC}  withAuth.tsx missing token expiry validation"
    fi
    echo ""
    
    # 5. JSDoc Comments Check
    echo "5. Checking JSDoc comments..."
    if grep -q "@example" src/components/forms/LoginForm.tsx 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} LoginForm.tsx has JSDoc comments"
    else
        echo -e "   ${YELLOW}⚠${NC}  LoginForm.tsx missing JSDoc comments"
    fi
    echo ""
    
    # 6. Sanitization Utilities Check
    echo "6. Checking sanitization utilities..."
    if grep -q "sanitizeInput" src/lib/utils/sanitize.ts 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Sanitization utilities created"
    else
        echo -e "   ${RED}✗${NC} Sanitization utilities missing"
        ERRORS=$((ERRORS + 1))
    fi
    echo ""
    
    # 7. Error Types Check
    echo "7. Checking structured error types..."
    if grep -q "ErrorCode" src/lib/types/errors.ts 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Structured error types created"
    else
        echo -e "   ${RED}✗${NC} Structured error types missing"
        ERRORS=$((ERRORS + 1))
    fi
    echo ""
fi

# =============================================================================
# Full Checks (Run Linter and Tests)
# =============================================================================

if [ "$FULL" = true ]; then
    echo -e "${YELLOW}Running Full Checks...${NC}"
    echo ""
    
    # 1. Run ESLint
    echo "1. Running ESLint..."
    if npm run lint:check > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} ESLint passed"
    else
        echo -e "   ${YELLOW}⚠${NC}  ESLint found issues (run 'npm run lint:check' for details)"
    fi
    echo ""
    
    # 2. Run TypeScript Compiler
    echo "2. Running TypeScript compiler..."
    if npx tsc --noEmit > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} TypeScript compilation successful"
    else
        echo -e "   ${RED}✗${NC} TypeScript compilation failed"
        ERRORS=$((ERRORS + 1))
    fi
    echo ""
    
    # 3. Run Tests
    echo "3. Running tests..."
    if npm test -- --passWithNoTests > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} Tests passed"
    else
        echo -e "   ${YELLOW}⚠${NC}  Some tests failed (run 'npm test' for details)"
    fi
    echo ""
fi

# =============================================================================
# Summary
# =============================================================================

echo -e "${BLUE}=================================="
echo "Verification Complete"
echo -e "==================================${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    
    if [ "$FULL" != true ]; then
        echo "To run comprehensive checks:"
        echo "  $0 --full"
    fi
    
    exit 0
else
    echo -e "${RED}✗ Found $ERRORS error(s)${NC}"
    echo ""
    echo "To fix issues:"
    echo "  npm run lint        # Fix linting issues"
    echo "  npx tsc --noEmit    # Check TypeScript errors"
    echo "  npm test            # Run tests"
    echo ""
    exit 1
fi
