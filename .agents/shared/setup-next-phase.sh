#!/bin/zsh
# setup-next-phase.sh - Set up coordination for Copilot after Task 1.4 completion
# Run this script manually once Task 1.4 is complete

set -e

echo "🚀 Phase 1 Next Step Setup"
echo "=========================="
echo ""

# Configuration
TODO_FILE="TODO.md"
TASK_ASSIGNMENTS=".agents/shared/task-assignments.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Task 1.4 is complete
echo "📋 Checking Task 1.4 completion status..."
COMPLETED=$(grep '\[x\].*1\.4\.' "$TODO_FILE" 2>/dev/null | wc -l)
COMPLETED="${COMPLETED// /}"
UNCHECKED=$(grep '\[ \].*1\.4\.' "$TODO_FILE" 2>/dev/null | wc -l)
UNCHECKED="${UNCHECKED// /}"
TOTAL=$((COMPLETED + UNCHECKED))

echo "  Found: $COMPLETED completed out of $TOTAL subtasks"
echo ""

if [ "$COMPLETED" -lt "$TOTAL" ]; then
  echo "${RED}❌ Task 1.4 is not complete yet!${NC}"
  echo ""
  echo "Remaining subtasks:"
  grep '\[ \].*1\.4\.' "$TODO_FILE" | head -5
  echo ""
  echo "Please complete all Task 1.4 subtasks before running this script."
  exit 1
fi

echo "${GREEN}✅ Task 1.4 is complete!${NC}"
echo ""

# Step 1: Create Git branches
echo "🌿 Step 1: Creating Git branches..."
echo "-----------------------------------"

if git rev-parse --verify agent/gemini/phase1-migrations >/dev/null 2>&1; then
  echo "  ℹ️  agent/gemini/phase1-migrations already exists"
else
  echo "  Creating agent/gemini/phase1-migrations..."
  git checkout -b agent/gemini/phase1-migrations
  echo "${GREEN}  ✅ Created agent/gemini/phase1-migrations${NC}"
  git checkout main
fi

if git rev-parse --verify agent/copilot/phase1-components >/dev/null 2>&1; then
  echo "  ℹ️  agent/copilot/phase1-components already exists"
else
  echo "  Creating agent/copilot/phase1-components..."
  git checkout -b agent/copilot/phase1-components
  echo "${GREEN}  ✅ Created agent/copilot/phase1-components${NC}"
  git checkout main
fi

if git rev-parse --verify phase1-integration >/dev/null 2>&1; then
  echo "  ℹ️  phase1-integration already exists"
else
  echo "  Creating phase1-integration..."
  git checkout -b phase1-integration
  echo "${GREEN}  ✅ Created phase1-integration${NC}"
  git checkout main
fi

echo ""

# Step 2: Update coordination file
echo "📝 Step 2: Updating coordination file..."
echo "----------------------------------------"

if command -v jq >/dev/null 2>&1; then
  # Use jq if available
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  
  jq --arg ts "$TIMESTAMP" '
    .last_updated = $ts |
    .agents.gemini.status = "idle" |
    .agents.gemini.completed_tasks = ["1.4.1","1.4.2","1.4.3","1.4.4","1.4.5","1.4.6"] |
    .agents.gemini.assigned_files = [] |
    .agents.gemini.current_task = null |
    .agents.copilot.status = "active" |
    .agents.copilot.current_task = "1.5.1" |
    .agents.copilot.blocked_by = null |
    .task_queue.in_progress = ["1.5.1"] |
    .task_queue.completed = ["1.4.1","1.4.2","1.4.3","1.4.4","1.4.5","1.4.6"]
  ' "$TASK_ASSIGNMENTS" > "$TASK_ASSIGNMENTS.tmp" && mv "$TASK_ASSIGNMENTS.tmp" "$TASK_ASSIGNMENTS"
  
  echo "${GREEN}  ✅ Updated task-assignments.json with jq${NC}"
else
  # Manual update without jq
  echo "${YELLOW}  ⚠️  jq not installed, showing manual update instructions:${NC}"
  echo ""
  echo "  Edit .agents/shared/task-assignments.json:"
  echo "  1. Set agents.gemini.status = \"idle\""
  echo "  2. Set agents.gemini.completed_tasks = [\"1.4.1\", ..., \"1.4.6\"]"
  echo "  3. Set agents.copilot.status = \"active\""
  echo "  4. Set agents.copilot.current_task = \"1.5.1\""
  echo "  5. Set agents.copilot.blocked_by = null"
  echo ""
  read -p "Press Enter after manually updating the file..."
fi

echo ""

# Step 3: Show next steps
echo "🎯 Step 3: Next Steps for Copilot"
echo "----------------------------------"
echo ""
echo "${BLUE}GitHub Copilot is now ready to start building components!${NC}"
echo ""
echo "Instructions:"
echo "  1. Checkout the Copilot branch:"
echo "     ${YELLOW}git checkout agent/copilot/phase1-components${NC}"
echo ""
echo "  2. Read the component builder guide:"
echo "     ${YELLOW}cat .agents/copilot/component-builder-instructions.md${NC}"
echo ""
echo "  3. Start with Task 1.5.1 (SkeletonText component)"
echo "     - Create: frontend/src/components/common/SkeletonText.tsx"
echo "     - Use design tokens from globals.css"
echo "     - Include variants, sizes, animations"
echo ""
echo "  4. After completing each component:"
echo "     ${YELLOW}git add .${NC}"
echo "     ${YELLOW}git commit -m \"feat(skeleton): add SkeletonText component\"${NC}"
echo ""
echo "  5. Monitor progress:"
echo "     ${YELLOW}.agents/shared/sync-check.sh${NC}"
echo ""

# Step 4: Summary
echo "📊 Setup Summary"
echo "----------------"
echo ""
echo "  ${GREEN}✅${NC} Task 1.4: Complete (all 6 subtasks)"
echo "  ${GREEN}✅${NC} Git branches: Created"
echo "  ${GREEN}✅${NC} Coordination file: Updated"
echo "  ${GREEN}✅${NC} Copilot: Ready to start"
echo ""
echo "  ${BLUE}→${NC} Next: Build 16 new components (Tasks 1.5-1.7)"
echo "  ${BLUE}→${NC} Timeline: ~8-10 hours for all components"
echo "  ${BLUE}→${NC} Files: All new (no conflicts with Gemini's work)"
echo ""

# Optional: Show current branch status
echo "🌿 Current Branch Status:"
echo "-------------------------"
git branch -vv | grep -E "(gemini|copilot|integration)" || echo "  Branches created successfully"
echo ""

echo "=========================="
echo "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo "Ready to start parallel development with GitHub Copilot."

exit 0
