#!/bin/zsh
# conflict-resolver.sh - Emergency conflict resolution
# Use when accidental file conflicts occur between agents

set -e

echo "🚨 Conflict Resolution Tool"
echo "==========================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
GEMINI_BRANCH="agent/gemini/phase1-migrations"
COPILOT_BRANCH="agent/copilot/phase1-components"
TASK_FILE=".agents/shared/task-assignments.json"

echo ""
echo "🔍 Analyzing conflicts..."

# Check for merge conflicts in progress
if [ -f ".git/MERGE_HEAD" ]; then
  echo "${RED}⚠️  Active merge conflict detected!${NC}"
  CONFLICTED_FILES=$(git diff --name-only --diff-filter=U)
  
  echo ""
  echo "Conflicted files:"
  echo "$CONFLICTED_FILES" | sed 's/^/  - /'
  
  echo ""
  echo "Resolution options:"
  echo "  1) Accept Gemini's version (migrations)"
  echo "  2) Accept Copilot's version (new components)"
  echo "  3) Manual merge (open in editor)"
  echo "  4) Abort merge"
  
  read "choice?Enter choice (1-4): "
  
  case $choice in
    1)
      echo "Accepting Gemini's version for all conflicts..."
      echo "$CONFLICTED_FILES" | xargs git checkout --theirs
      git add .
      echo "${GREEN}✅ Resolved with Gemini's changes${NC}"
      ;;
    2)
      echo "Accepting Copilot's version for all conflicts..."
      echo "$CONFLICTED_FILES" | xargs git checkout --ours
      git add .
      echo "${GREEN}✅ Resolved with Copilot's changes${NC}"
      ;;
    3)
      echo "Opening conflicts in VS Code..."
      code --wait $(echo "$CONFLICTED_FILES" | tr '\n' ' ')
      echo "After resolving, run: git add . && git commit"
      ;;
    4)
      echo "Aborting merge..."
      git merge --abort
      echo "${YELLOW}⚠️  Merge aborted${NC}"
      exit 0
      ;;
    *)
      echo "${RED}Invalid choice${NC}"
      exit 1
      ;;
  esac
  
  exit 0
fi

# Check for potential conflicts (files modified in both branches)
echo ""
echo "🔍 Checking for potential conflicts..."

if ! git rev-parse --verify "$GEMINI_BRANCH" >/dev/null 2>&1; then
  echo "${YELLOW}⚠️  Gemini branch doesn't exist yet${NC}"
  exit 0
fi

if ! git rev-parse --verify "$COPILOT_BRANCH" >/dev/null 2>&1; then
  echo "${YELLOW}⚠️  Copilot branch doesn't exist yet${NC}"
  exit 0
fi

# Find files modified in both branches
GEMINI_FILES=$(git diff --name-only main "$GEMINI_BRANCH" | sort)
COPILOT_FILES=$(git diff --name-only main "$COPILOT_BRANCH" | sort)

SHARED_FILES=$(comm -12 <(echo "$GEMINI_FILES") <(echo "$COPILOT_FILES"))

if [ -z "$SHARED_FILES" ]; then
  echo "${GREEN}✅ No conflicts detected - agents working on different files${NC}"
  exit 0
fi

echo "${YELLOW}⚠️  Warning: Files modified by both agents:${NC}"
echo "$SHARED_FILES" | sed 's/^/  - /'

echo ""
echo "Analysis:"
for file in $SHARED_FILES; do
  echo ""
  echo "File: $file"
  
  # Determine which agent should own this file
  if echo "$file" | grep -q "frontend/src/components/ui/.*\.tsx" && ! git ls-tree -r "$GEMINI_BRANCH" --name-only | grep -q "$file"; then
    echo "  → ${GREEN}Copilot should own${NC} (new component)"
  elif echo "$file" | grep -q "frontend/src/components/.*" && git ls-tree -r main --name-only | grep -q "$file"; then
    echo "  → ${GREEN}Gemini should own${NC} (existing component migration)"
  else
    echo "  → ${YELLOW}Unclear ownership - manual review needed${NC}"
  fi
  
  # Show diff summary
  GEMINI_CHANGES=$(git diff main "$GEMINI_BRANCH" -- "$file" | grep -c '^+' || echo "0")
  COPILOT_CHANGES=$(git diff main "$COPILOT_BRANCH" -- "$file" | grep -c '^+' || echo "0")
  echo "  Gemini: +$GEMINI_CHANGES lines"
  echo "  Copilot: +$COPILOT_CHANGES lines"
done

echo ""
echo "Recommended Actions:"
echo "--------------------"
echo "1. Review file ownership in coordination-rules.md"
echo "2. Revert changes from the agent that shouldn't modify this file"
echo "3. Update file_locks in task-assignments.json"
echo "4. Establish clearer task boundaries"

echo ""
echo "Prevention:"
echo "-----------"
echo "• Gemini should only modify existing files from Task 1.4"
echo "• Copilot should only create new files from Tasks 1.5-1.7"
echo "• Always update file_locks before starting work"

exit 1
