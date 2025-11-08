# Agent Coordination Rules

## Overview
This coordination system allows Gemini CLI and GitHub Copilot to work in parallel on Phase 1 tasks without conflicts.

## Strategy: File-Level Task Partitioning

### Gemini CLI Responsibilities
- **Task 1.4**: Migration of existing components to design tokens
- **Files**: Modifies existing components (18 files)
- **Branch**: `agent/gemini/phase1-migrations`
- **Duration**: Currently in progress

### GitHub Copilot Responsibilities  
- **Tasks 1.5-1.7**: Building new components
- **Files**: Creates new files only (no conflicts)
- **Branch**: `agent/copilot/phase1-components`
- **Start**: After Task 1.4 complete

## File Lock Protocol

### Before Starting Work
1. Check `task-assignments.json` for file locks
2. If file is in another agent's `assigned_files`, WAIT
3. Add file path to your `assigned_files` before modifying
4. Update `current_task` field

### After Completing Work
1. Remove file from `assigned_files`
2. Add task ID to `completed_tasks`
3. Update `last_updated` timestamp
4. Commit with conventional commit message

## Branch Strategy

```
main
├── agent/gemini/phase1-migrations    (Gemini's work)
├── agent/copilot/phase1-components   (Copilot's work)
└── phase1-integration                (Daily merge of both)
```

### Workflow
1. Agents work on their respective branches
2. Daily integration merge to `phase1-integration`
3. Test integration branch
4. If tests pass, continue; if fail, resolve conflicts
5. Final merge to `main` when Phase 1 complete

## Task Claiming Process

### For Gemini CLI
```bash
# Update task-assignments.json before starting
{
  "agents": {
    "gemini": {
      "assigned_files": ["frontend/src/components/layout/Navigation.tsx"],
      "current_task": "1.4.2"
    }
  },
  "file_locks": {
    "frontend/src/components/layout/Navigation.tsx": "gemini"
  }
}
```

### For GitHub Copilot
```bash
# Copilot works on NEW files only (no locks needed)
{
  "agents": {
    "copilot": {
      "assigned_files": ["frontend/src/components/ui/Input.tsx"],
      "current_task": "1.6.1"
    }
  }
}
```

## Conflict Resolution Rules

### If Both Agents Need Same File
1. **Migration tasks (1.4.x)**: Gemini has PRIORITY
2. **New components (1.5-1.7)**: Copilot has PRIORITY
3. **Storybook tasks (1.8-1.9)**: WAIT until components ready

### Conflict Prevention
- Gemini: Only modifies existing files from Task 1.4
- Copilot: Only creates new files from Tasks 1.5-1.7
- **Result**: Zero file conflicts by design

## Daily Sync Checkpoints

### Every 4 Hours
Run `sync-check.sh` to verify:
- ✅ No file conflicts
- ✅ Task progress on track
- ✅ File locks released properly

### End of Day
Run `daily-integration.sh` to:
- Merge both branches to `phase1-integration`
- Run tests and linting
- Report integration status

## Communication Protocol

### Status Updates
Update `task-assignments.json` after each task:
```json
{
  "last_updated": "2025-11-08T14:30:00Z",
  "agents": {
    "gemini": {
      "status": "active",
      "completed_tasks": ["1.4.1", "1.4.2"]
    }
  }
}
```

### Blocked Situations
If blocked, update status:
```json
{
  "agents": {
    "copilot": {
      "status": "blocked",
      "blocked_by": "waiting for Task 1.4 completion",
      "blocked_since": "2025-11-08T10:00:00Z"
    }
  }
}
```

## Quality Gates

### Before Committing
- ✅ Linter passes: `cd frontend && npm run lint`
- ✅ Tests pass: `cd frontend && npm test`
- ✅ File locks released in `task-assignments.json`
- ✅ Conventional commit message used

### Commit Message Format
```
feat(migration): migrate Navigation to design tokens
feat(component): add Input component with variants
fix(migration): correct color token in JobTableView
```

## Emergency Procedures

### If Accidental Conflict Occurs
1. Stop both agents immediately
2. Run `conflict-resolver.sh`
3. Choose resolution strategy:
   - Accept Gemini's version (for migrations)
   - Accept Copilot's version (for new components)
   - Manual merge (if complex)
4. Update coordination rules to prevent recurrence

### If Integration Tests Fail
1. Identify failing component
2. Determine which agent's change caused failure
3. Revert problematic change
4. Fix and re-test
5. Document issue in `coordination-issues.log`

## Success Metrics

Track in `metrics.json`:
- Tasks completed per agent
- Conflicts encountered (target: 0)
- Integration builds (target: 100% pass rate)
- API usage (stay within free tiers)

## File Ownership Map

### Gemini CLI Owns (Task 1.4)
```
frontend/src/components/layout/Navigation.tsx
frontend/src/components/pages/JobTableView.tsx
frontend/src/components/common/ErrorBoundary.tsx
frontend/src/components/notifications/NotificationSystem.tsx
+ 15 files for Button import updates
```

### Copilot Owns (Tasks 1.5-1.7)
```
frontend/src/components/common/SkeletonText.tsx (NEW)
frontend/src/components/common/SkeletonCard.tsx (NEW)
frontend/src/components/ui/Input.tsx (NEW)
frontend/src/components/ui/Select.tsx (NEW)
frontend/src/components/ui/Modal.tsx (NEW)
+ 10 more new component files
```

### No Overlap = No Conflicts ✅
