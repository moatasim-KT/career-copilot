#!/bin/zsh
# monitor-task-1.4.sh - Monitor Task 1.4 completion and trigger next phase
# Run this script to continuously monitor Task 1.4 progress

set -e

echo "📊 Task 1.4 Monitoring System"
echo "=============================="
echo ""

# Configuration
TODO_FILE="TODO.md"
TASK_ASSIGNMENTS=".agents/shared/task-assignments.json"
CHECK_INTERVAL=300  # 5 minutes

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to count completed subtasks
count_completed() {
  local count=$(grep -E '\[x\].*1\.4\.' "$TODO_FILE" 2>/dev/null | wc -l)
  echo "${count// /}"
}

# Function to count total subtasks
count_total() {
  local checked=$(count_completed)
  local unchecked=$(grep -E '\[ \].*1\.4\.' "$TODO_FILE" 2>/dev/null | wc -l)
  unchecked="${unchecked// /}"
  echo $((checked + unchecked))
}

# Function to show progress bar
show_progress() {
  local completed=$1
  local total=$2
  
  # Avoid division by zero
  if [ "$total" -eq 0 ]; then
    echo "Progress: No tasks found"
    return
  fi
  
  local percent=$((completed * 100 / total))
  local filled=$((percent / 5))
  local empty=$((20 - filled))
  
  printf "Progress: ["
  printf "%${filled}s" | tr ' ' '='
  printf "%${empty}s" | tr ' ' '-'
  printf "] %d%% (%d/%d)\n" "$percent" "$completed" "$total"
}

# Initial check
echo "Checking TODO.md for Task 1.4 status..."
echo ""

TOTAL=$(count_total)
COMPLETED=$(count_completed)

if [ "$TOTAL" -eq 0 ]; then
  echo "${YELLOW}⚠️  Warning: No Task 1.4 subtasks found in TODO.md${NC}"
  echo "Make sure TODO.md contains Task 1.4 subtasks (1.4.1 through 1.4.6)"
  exit 1
fi

echo "Found $TOTAL Task 1.4 subtasks in TODO.md"
echo "Currently $COMPLETED completed"
echo ""

# Monitoring loop
echo "Starting continuous monitoring..."
echo "Press Ctrl+C to stop"
echo ""

LAST_COMPLETED=-1

while true; do
  COMPLETED=$(count_completed)
  
  # Only update if progress changed
  if [ "$COMPLETED" -ne "$LAST_COMPLETED" ]; then
    clear
    echo "📊 Task 1.4 Monitoring System"
    echo "=============================="
    echo ""
    echo "$(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    show_progress "$COMPLETED" "$TOTAL"
    echo ""
    
    # List completed subtasks
    if [ "$COMPLETED" -gt 0 ]; then
      echo "${GREEN}✅ Completed:${NC}"
      grep -E '\[x\].*1\.4\.' "$TODO_FILE" | sed 's/^/  /' | sed 's/\[x\]/✓/'
      echo ""
    fi
    
    # List remaining subtasks
    REMAINING=$((TOTAL - COMPLETED))
    if [ "$REMAINING" -gt 0 ]; then
      echo "${BLUE}⏳ Remaining ($REMAINING):${NC}"
      grep -E '\[ \].*1\.4\.' "$TODO_FILE" | sed 's/^/  /' | head -n 5
      if [ "$REMAINING" -gt 5 ]; then
        echo "  ... and $((REMAINING - 5)) more"
      fi
      echo ""
    fi
    
    LAST_COMPLETED=$COMPLETED
    
    # Check if Task 1.4 is complete
    if [ "$COMPLETED" -eq "$TOTAL" ]; then
      echo ""
      echo "${GREEN}🎉 Task 1.4 Complete!${NC}"
      echo "=============================="
      echo ""
      echo "All $TOTAL subtasks have been completed by Gemini CLI"
      echo ""
      echo "Next steps:"
      echo "  1. Create Git branches (if not already created)"
      echo "  2. Update task-assignments.json"
      echo "  3. Start Copilot on Task 1.5"
      echo ""
      
      # Offer to trigger next phase automatically
      echo "Would you like to automatically trigger the next phase? (y/n)"
      read -r REPLY
      
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Triggering next phase setup..."
        
        # Create branches if they don't exist
        if ! git rev-parse --verify agent/gemini/phase1-migrations >/dev/null 2>&1; then
          echo "Creating agent/gemini/phase1-migrations branch..."
          git checkout -b agent/gemini/phase1-migrations
          git checkout main
        fi
        
        if ! git rev-parse --verify agent/copilot/phase1-components >/dev/null 2>&1; then
          echo "Creating agent/copilot/phase1-components branch..."
          git checkout -b agent/copilot/phase1-components
          git checkout main
        fi
        
        if ! git rev-parse --verify phase1-integration >/dev/null 2>&1; then
          echo "Creating phase1-integration branch..."
          git checkout -b phase1-integration
          git checkout main
        fi
        
        # Update task assignments
        if command -v jq &> /dev/null && [ -f "$TASK_ASSIGNMENTS" ]; then
          echo "Updating task-assignments.json..."
          
          jq '.agents.gemini.status = "idle" | 
              .agents.gemini.completed_tasks = ["1.4.1","1.4.2","1.4.3","1.4.4","1.4.5","1.4.6"] |
              .agents.copilot.status = "active" |
              .agents.copilot.current_task = "1.5.1" |
              .agents.copilot.blocked_by = null |
              .last_updated = now | strftime("%Y-%m-%dT%H:%M:%SZ")' \
              "$TASK_ASSIGNMENTS" > "$TASK_ASSIGNMENTS.tmp" && \
              mv "$TASK_ASSIGNMENTS.tmp" "$TASK_ASSIGNMENTS"
          
          echo "${GREEN}✅ Updated task-assignments.json${NC}"
        fi
        
        echo ""
        echo "${GREEN}✅ Next phase setup complete!${NC}"
        echo ""
        echo "GitHub Copilot can now start working on Task 1.5"
        echo "Instructions: .agents/copilot/component-builder-instructions.md"
      else
        echo "Skipping automatic setup. Update manually when ready."
      fi
      
      break
    fi
  fi
  
  # Wait before next check
  sleep $CHECK_INTERVAL
done

echo ""
echo "Monitoring stopped."
