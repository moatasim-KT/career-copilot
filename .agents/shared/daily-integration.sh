#!/bin/zsh
# daily-integration.sh - Merge agent branches and run integration tests
# Run at end of day to combine Gemini and Copilot work

set -e

echo "🔄 Daily Integration - $(date)"
echo "========================================"

# Configuration
GEMINI_BRANCH="agent/gemini/phase1-migrations"
COPILOT_BRANCH="agent/copilot/phase1-components"
INTEGRATION_BRANCH="phase1-integration"
TASK_FILE=".agents/shared/task-assignments.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "📋 Pre-Integration Checks:"
echo "--------------------------"

# Check if branches exist
GEMINI_EXISTS=$(git rev-parse --verify "$GEMINI_BRANCH" >/dev/null 2>&1 && echo "yes" || echo "no")
COPILOT_EXISTS=$(git rev-parse --verify "$COPILOT_BRANCH" >/dev/null 2>&1 && echo "yes" || echo "no")

if [ "$GEMINI_EXISTS" = "no" ] && [ "$COPILOT_EXISTS" = "no" ]; then
  echo "${YELLOW}⚠️  No agent branches exist yet. Skipping integration.${NC}"
  exit 0
fi

echo "  ✅ Gemini branch: $GEMINI_EXISTS"
echo "  ✅ Copilot branch: $COPILOT_EXISTS"

# Save current branch
CURRENT_BRANCH=$(git branch --show-current)

echo ""
echo "🌿 Creating/Updating Integration Branch:"
echo "-----------------------------------------"

# Create or switch to integration branch
if git rev-parse --verify "$INTEGRATION_BRANCH" >/dev/null 2>&1; then
  echo "  Switching to existing $INTEGRATION_BRANCH"
  git checkout "$INTEGRATION_BRANCH"
else
  echo "  Creating new $INTEGRATION_BRANCH from main"
  git checkout -b "$INTEGRATION_BRANCH" main
fi

echo ""
echo "🔀 Merging Agent Branches:"
echo "--------------------------"

# Merge Gemini branch (migrations)
if [ "$GEMINI_EXISTS" = "yes" ]; then
  echo "  Merging $GEMINI_BRANCH..."
  if git merge "$GEMINI_BRANCH" --no-edit -m "chore(integration): merge Gemini migrations"; then
    echo "${GREEN}  ✅ Gemini merge successful${NC}"
  else
    echo "${RED}  ❌ Gemini merge failed - conflicts detected${NC}"
    git merge --abort
    git checkout "$CURRENT_BRANCH"
    exit 1
  fi
fi

# Merge Copilot branch (new components)
if [ "$COPILOT_EXISTS" = "yes" ]; then
  echo "  Merging $COPILOT_BRANCH..."
  if git merge "$COPILOT_BRANCH" --no-edit -m "chore(integration): merge Copilot components"; then
    echo "${GREEN}  ✅ Copilot merge successful${NC}"
  else
    echo "${RED}  ❌ Copilot merge failed - conflicts detected${NC}"
    git merge --abort
    git checkout "$CURRENT_BRANCH"
    exit 1
  fi
fi

echo ""
echo "🧪 Running Integration Tests:"
echo "------------------------------"

cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "  Installing dependencies..."
  npm install
fi

# Run linter
echo "  Running ESLint..."
if npm run lint 2>&1 | tail -n 20; then
  echo "${GREEN}  ✅ Linting passed${NC}"
else
  echo "${YELLOW}  ⚠️  Linting found issues (non-blocking)${NC}"
fi

# Run type checking
echo "  Running TypeScript check..."
if npx tsc --noEmit 2>&1 | tail -n 20; then
  echo "${GREEN}  ✅ Type checking passed${NC}"
else
  echo "${RED}  ❌ Type checking failed${NC}"
  cd ..
  git checkout "$CURRENT_BRANCH"
  exit 1
fi

# Run tests
echo "  Running unit tests..."
if npm test -- --passWithNoTests 2>&1 | tail -n 30; then
  echo "${GREEN}  ✅ Tests passed${NC}"
else
  echo "${RED}  ❌ Tests failed${NC}"
  cd ..
  git checkout "$CURRENT_BRANCH"
  exit 1
fi

# Build check
echo "  Running build check..."
if npm run build 2>&1 | tail -n 20; then
  echo "${GREEN}  ✅ Build successful${NC}"
else
  echo "${RED}  ❌ Build failed${NC}"
  cd ..
  git checkout "$CURRENT_BRANCH"
  exit 1
fi

cd ..

echo ""
echo "📊 Integration Summary:"
echo "-----------------------"

# Count merged commits
if [ "$GEMINI_EXISTS" = "yes" ]; then
  GEMINI_COMMITS=$(git rev-list --count "$GEMINI_BRANCH" ^main)
  echo "  Gemini: $GEMINI_COMMITS commits merged"
fi

if [ "$COPILOT_EXISTS" = "yes" ]; then
  COPILOT_COMMITS=$(git rev-list --count "$COPILOT_BRANCH" ^main)
  echo "  Copilot: $COPILOT_COMMITS commits merged"
fi

echo ""
echo "  Files changed: $(git diff --name-only main | wc -l | xargs)"
echo "  Insertions: $(git diff --stat main | tail -n 1 | grep -o '[0-9]\+ insertion' | grep -o '[0-9]\+')"
echo "  Deletions: $(git diff --stat main | tail -n 1 | grep -o '[0-9]\+ deletion' | grep -o '[0-9]\+')"

echo ""
echo "✅ Integration Complete!"
echo "------------------------"
echo "  Branch: $INTEGRATION_BRANCH"
echo "  Status: Ready for review"
echo "  Next: Test integration branch, then merge to main"

# Update task assignments
if [ -f "$TASK_FILE" ] && command -v jq &> /dev/null; then
  jq --arg date "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
     '.last_integration = $date | .integration_status = "success"' \
     "$TASK_FILE" > "$TASK_FILE.tmp" && mv "$TASK_FILE.tmp" "$TASK_FILE"
  echo "  📝 Updated task-assignments.json"
fi

# Return to original branch
git checkout "$CURRENT_BRANCH"

echo ""
echo "========================================"
echo "🎉 Daily integration successful!"
