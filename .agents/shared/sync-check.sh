#!/bin/zsh
# sync-check.sh - Coordination health check (run every 4 hours)
# Monitors agent status, detects conflicts, verifies file locks

set -e

echo "🔍 Agent Coordination Sync Check - $(date)"
echo "============================================"

# Configuration
TASK_FILE=".agents/shared/task-assignments.json"
GEMINI_BRANCH="agent/gemini/phase1-migrations"
COPILOT_BRANCH="agent/copilot/phase1-components"

# Check if coordination file exists
if [ ! -f "$TASK_FILE" ]; then
  echo "❌ ERROR: task-assignments.json not found!"
  exit 1
fi

echo ""
echo "📊 Agent Status:"
echo "----------------"

# Extract agent statuses using jq (if available) or fallback to grep
if command -v jq &> /dev/null; then
  GEMINI_STATUS=$(jq -r '.agents.gemini.status' "$TASK_FILE")
  COPILOT_STATUS=$(jq -r '.agents.copilot.status' "$TASK_FILE")
  GEMINI_TASK=$(jq -r '.agents.gemini.current_task' "$TASK_FILE")
  COPILOT_TASK=$(jq -r '.agents.copilot.current_task' "$TASK_FILE")
  
  echo "  Gemini CLI:  $GEMINI_STATUS (Task: $GEMINI_TASK)"
  echo "  Copilot:     $COPILOT_STATUS (Task: $COPILOT_TASK)"
else
  echo "  ⚠️  jq not installed - showing raw status"
  grep -A 2 '"gemini":' "$TASK_FILE"
  grep -A 2 '"copilot":' "$TASK_FILE"
fi

echo ""
echo "🔒 File Lock Status:"
echo "--------------------"

# Check for file locks
LOCKED_FILES=$(grep -A 10 '"file_locks":' "$TASK_FILE" | grep -v "file_locks" | grep -v "^--$" | wc -l)
LOCKED_FILES="${LOCKED_FILES// /}"

if [ "$LOCKED_FILES" -eq 0 ]; then
  echo "  ✅ No files currently locked"
else
  echo "  📝 $LOCKED_FILES file(s) locked:"
  if command -v jq &> /dev/null; then
    jq -r '.file_locks | to_entries[] | "    - \(.key) (locked by: \(.value))"' "$TASK_FILE"
  else
    grep -A 10 '"file_locks":' "$TASK_FILE"
  fi
fi

echo ""
echo "🌿 Git Branch Status:"
echo "---------------------"

# Check if branches exist
if git rev-parse --verify "$GEMINI_BRANCH" >/dev/null 2>&1; then
  GEMINI_COMMITS=$(git rev-list --count "$GEMINI_BRANCH" ^main 2>/dev/null || echo "0")
  GEMINI_COMMITS="${GEMINI_COMMITS// /}"
  echo "  ✅ $GEMINI_BRANCH: $GEMINI_COMMITS commits ahead of main"
else
  echo "  ⚠️  $GEMINI_BRANCH: Not created yet"
fi

if git rev-parse --verify "$COPILOT_BRANCH" >/dev/null 2>&1; then
  COPILOT_COMMITS=$(git rev-list --count "$COPILOT_BRANCH" ^main 2>/dev/null || echo "0")
  COPILOT_COMMITS="${COPILOT_COMMITS// /}"
  echo "  ✅ $COPILOT_BRANCH: $COPILOT_COMMITS commits ahead of main"
else
  echo "  ⚠️  $COPILOT_BRANCH: Not created yet"
fi

echo ""
echo "⚠️  Conflict Detection:"
echo "-----------------------"

# Check for potential conflicts (files modified in both branches)
if git rev-parse --verify "$GEMINI_BRANCH" >/dev/null 2>&1 && git rev-parse --verify "$COPILOT_BRANCH" >/dev/null 2>&1; then
  CONFLICTS=$(git diff --name-only "$GEMINI_BRANCH" "$COPILOT_BRANCH" 2>/dev/null | wc -l)
  CONFLICTS="${CONFLICTS// /}"
  
  if [ "$CONFLICTS" -eq 0 ]; then
    echo "  ✅ No conflicts detected"
  else
    echo "  ⚠️  $CONFLICTS file(s) differ between branches:"
    git diff --name-only "$GEMINI_BRANCH" "$COPILOT_BRANCH" | sed 's/^/    - /'
  fi
else
  echo "  ℹ️  Branches not ready for conflict check"
fi

echo ""
echo "📈 Task Progress:"
echo "-----------------"

if command -v jq &> /dev/null; then
  echo "  Queue Status:"
  IN_PROGRESS=$(jq -r '.task_queue.in_progress | length' "$TASK_FILE")
  READY=$(jq -r '.task_queue.ready_for_copilot | length' "$TASK_FILE")
  BLOCKED=$(jq -r '.task_queue.blocked | length' "$TASK_FILE")
  
  echo "    • In Progress: $IN_PROGRESS tasks"
  echo "    • Ready for Copilot: $READY tasks"
  echo "    • Blocked: $BLOCKED tasks"
  
  echo ""
  echo "  Completed Tasks:"
  GEMINI_DONE=$(jq -r '.agents.gemini.completed_tasks | length' "$TASK_FILE")
  COPILOT_DONE=$(jq -r '.agents.copilot.completed_tasks | length' "$TASK_FILE")
  echo "    • Gemini: $GEMINI_DONE tasks"
  echo "    • Copilot: $COPILOT_DONE tasks"
fi

echo ""
echo "🕒 Last Update:"
echo "---------------"

if command -v jq &> /dev/null; then
  LAST_UPDATE=$(jq -r '.last_updated' "$TASK_FILE")
  echo "  $LAST_UPDATE"
  
  # Calculate time since last update (macOS compatible)
  LAST_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_UPDATE" +%s 2>/dev/null || echo "0")
  NOW_TS=$(date +%s)
  DIFF=$((NOW_TS - LAST_TS))
  HOURS=$((DIFF / 3600))
  
  if [ "$HOURS" -gt 8 ]; then
    echo "  ⚠️  Warning: No updates in $HOURS hours"
  elif [ "$HOURS" -gt 0 ]; then
    echo "  ✅ Updated $HOURS hour(s) ago"
  else
    MINUTES=$((DIFF / 60))
    echo "  ✅ Updated $MINUTES minute(s) ago"
  fi
fi

echo ""
echo "============================================"
echo "Sync check complete ✅"
echo ""

# Return appropriate exit code
if [ "$LOCKED_FILES" -gt 5 ]; then
  echo "⚠️  Warning: Many files locked ($LOCKED_FILES)"
  exit 1
elif [ "$CONFLICTS" -gt 0 ]; then
  echo "⚠️  Warning: Conflicts detected ($CONFLICTS)"
  exit 1
else
  exit 0
fi
