#!/bin/zsh
# quick-status.sh - Quick status check for coordination system

echo "📊 Career Copilot - Agent Coordination Status"
echo "=============================================="
echo ""

# Check Task 1.4 status
echo "Task 1.4 Status:"
if grep -q "### ✅ Task 1.4.*\[COMPLETE\]" TODO.md; then
  echo "  ✅ COMPLETE"
else
  echo "  ⏳ In Progress"
fi
echo ""

# Check branches
echo "Git Branches:"
if git rev-parse --verify agent/gemini/phase1-migrations >/dev/null 2>&1; then
  echo "  ✅ agent/gemini/phase1-migrations exists"
else
  echo "  ❌ agent/gemini/phase1-migrations not created"
fi

if git rev-parse --verify agent/copilot/phase1-components >/dev/null 2>&1; then
  echo "  ✅ agent/copilot/phase1-components exists"
else
  echo "  ❌ agent/copilot/phase1-components not created"
fi

if git rev-parse --verify phase1-integration >/dev/null 2>&1; then
  echo "  ✅ phase1-integration exists"
else
  echo "  ❌ phase1-integration not created"
fi
echo ""

# Check coordination file
if [ -f ".agents/shared/task-assignments.json" ]; then
  echo "Coordination Status:"
  if command -v jq >/dev/null 2>&1; then
    echo "  Gemini: $(jq -r '.agents.gemini.status' .agents/shared/task-assignments.json)"
    echo "  Copilot: $(jq -r '.agents.copilot.status' .agents/shared/task-assignments.json)"
  else
    echo "  (Install jq for detailed status)"
  fi
  echo ""
fi

# Check current branch
CURRENT=$(git branch --show-current)
echo "Current Branch: $CURRENT"
echo ""

# Show next steps
if grep -q "### ✅ Task 1.4.*\[COMPLETE\]" TODO.md && \
   git rev-parse --verify agent/copilot/phase1-components >/dev/null 2>&1; then
  echo "🎯 Next Steps:"
  echo "  1. Checkout Copilot branch:"
  echo "     git checkout agent/copilot/phase1-components"
  echo ""
  echo "  2. Read instructions:"
  echo "     cat .agents/copilot/component-builder-instructions.md"
  echo ""
  echo "  3. Start building Task 1.5.1 (SkeletonText)"
elif grep -q "### ✅ Task 1.4.*\[COMPLETE\]" TODO.md; then
  echo "🎯 Next Steps:"
  echo "  Run setup script to create branches:"
  echo "  .agents/shared/setup-next-phase.sh"
else
  echo "🎯 Next Steps:"
  echo "  Wait for Task 1.4 to complete"
  echo "  (Currently being done by Gemini CLI)"
fi
