# Agent Coordination System
**Version**: 1.0.0  
**Strategy**: File-Level Task Partitioning  
**Agents**: Gemini CLI + GitHub Copilot

---

## Quick Start

### 1. Check Current Status
```bash
.agents/shared/quick-status.sh
```

### 2. Start Building Components (Task 1.4 Already Complete ✅)
```bash
# Switch to Copilot branch
git checkout agent/copilot/phase1-components

# Read component builder instructions
cat .agents/copilot/component-builder-instructions.md

# Start with Task 1.5.1 (SkeletonText)
```

### 3. Daily Integration
```bash
.agents/shared/daily-integration.sh
```

### 4. If Conflicts Occur
```bash
.agents/shared/conflict-resolver.sh
```

---

## Directory Structure

```
.agents/
├── README.md (this file)
├── gemini/
│   ├── migration-prompt-template.txt  # Prompts for Gemini CLI
│   └── completed/                     # Archive of completed migrations
├── copilot/
│   ├── component-builder-instructions.md  # Instructions for Copilot
│   └── completed/                        # Archive of completed components
└── shared/
    ├── task-assignments.json          # Real-time coordination state
    ├── coordination-rules.md          # Detailed coordination rules
    ├── task-partition-plan.md         # Task and file assignments
    ├── sync-check.sh                  # Health check script (run every 4 hours)
    ├── daily-integration.sh           # Daily merge and test script
    └── conflict-resolver.sh           # Emergency conflict resolution
```

---

## How It Works

### File-Level Task Partitioning

**Core Principle**: Different files = Zero conflicts

- **Gemini CLI**: Modifies existing 18 files (Task 1.4 migrations)
- **GitHub Copilot**: Creates 16 new files (Tasks 1.5-1.7 components)
- **Result**: No merge conflicts by design

### Coordination Flow

```
┌─────────────┐
│  Task 1.4   │  ← Gemini CLI (IN PROGRESS)
│  Migrations │     Modifying existing files
└─────────────┘
      ↓ Complete
┌─────────────────────────────┐
│  Task 1.5-1.7 Components    │  ← Copilot (WAITING)
│  Skeleton, Input, Modal     │     Creating new files
└─────────────────────────────┘
      ↓ Both complete
┌─────────────────────────────┐
│  Daily Integration          │
│  Merge both branches        │
└─────────────────────────────┘
      ↓ Tests pass
┌─────────────────────────────┐
│  Phase 1 Complete ✅        │
└─────────────────────────────┘
```

---

## Usage Guide

### For Gemini CLI

**Current Status**: ✅ Task 1.4 Complete - Idle

**Completed Work**:
- ✅ All 18 files migrated to design tokens
- ✅ Button → Button2 imports updated
- ✅ Navigation, JobTableView, ErrorBoundary migrated
- ✅ All changes committed to main branch

**Archived**:
- Migration prompt template in `gemini/migration-prompt-template.txt` (for reference)
- Files modified are now in git history

**Available for Future Tasks**:
- Can be assigned Phase 2+ tasks when ready
- Can assist with testing/review of Copilot's components

---

### For GitHub Copilot

**Current Status**: ✅ Active - Ready to Build

**Instructions**:
1. ✅ Task 1.4 already complete (no waiting needed)
2. Read `copilot/component-builder-instructions.md`
3. Checkout branch: `git checkout agent/copilot/phase1-components`
4. Start with Task 1.5.1 (SkeletonText component)
5. Update `shared/task-assignments.json` when starting/completing tasks
6. Commit with: `feat(component): add [ComponentName] with variants`

**Files You Can Create** (16 new files):
- See `shared/task-partition-plan.md` Section: "GitHub Copilot - File Ownership"

**Files You CANNOT Touch**:
- Any file from Gemini's list (existing components)
- Files modified in Task 1.4

---

## Monitoring & Health Checks

### Automated Checks

```bash
# Every 4 hours (manual or cron)
*/240 * * * * cd /path/to/career-copilot && .agents/shared/sync-check.sh
```

### Daily Integration

```bash
# End of day (18:00)
0 18 * * * cd /path/to/career-copilot && .agents/shared/daily-integration.sh
```

### Manual Checks

```bash
# Check agent status
cat .agents/shared/task-assignments.json | jq '.agents'

# Check file locks
cat .agents/shared/task-assignments.json | jq '.file_locks'

# Check task progress
cat .agents/shared/task-assignments.json | jq '.task_queue'

# See Git branch status
git branch -vv
```

---

## Key Files Explained

### task-assignments.json
**Purpose**: Real-time coordination state  
**Updated By**: Both agents  
**Update Frequency**: Every time task starts/completes  
**Critical Fields**:
- `agents.*.status`: "active", "waiting_for_1.4", "idle", "blocked"
- `agents.*.current_task`: Current task ID (e.g., "1.4.2")
- `file_locks`: Which files are being modified right now
- `task_queue`: What's in progress, ready, or blocked

### coordination-rules.md
**Purpose**: Detailed coordination protocol  
**Read By**: Both agents (reference document)  
**Contains**:
- File lock protocol
- Branch strategy
- Task claiming process
- Conflict prevention rules
- Daily sync checkpoints
- Emergency procedures

### task-partition-plan.md
**Purpose**: Complete task and file assignment map  
**Read By**: Both agents (planning document)  
**Contains**:
- Exact file ownership (18 for Gemini, 16 for Copilot)
- Task assignments and timing
- Timeline estimates
- Success metrics

---

## Success Metrics

### Target Goals
- **Phase 1 Duration**: 3-4 days (vs 10-14 sequential)
- **Speedup**: 4-5x faster
- **Conflicts**: 0 (by design)
- **Integration Pass Rate**: 100%
- **Cost**: $0 (free tiers only)

### Current Progress
Check TODO.md for real-time task completion:
```bash
grep -E '\[x\].*1\.4\.' TODO.md | wc -l  # Gemini completed
grep -E '\[x\].*1\.(5|6|7)\.' TODO.md | wc -l  # Copilot completed
```

---

## Troubleshooting

### "Sync check shows conflicts"
```bash
.agents/shared/conflict-resolver.sh
# Follow prompts to resolve
```

### "Task 1.4 taking too long"
- Check Gemini CLI API usage limits (1500 req/day)
- Consider splitting Task 1.4.6 (comprehensive sweep) into smaller chunks
- Update `task-assignments.json` with realistic timeline

### "Copilot started before Task 1.4 complete"
```bash
# Stop Copilot work
git checkout agent/copilot/phase1-components
git reset --hard main  # IF no valuable work yet

# Wait for Gemini to finish
# Then restart Copilot
```

### "Integration tests failing"
1. Check which branch caused failure:
   ```bash
   git bisect start
   git bisect bad phase1-integration
   git bisect good main
   ```
2. Identify problematic commit
3. Revert and fix
4. Re-run daily-integration.sh

---

## Next Steps

### Current Status (Task 1.4 Already Complete ✅)
- [x] Task 1.4 complete and committed
- [x] Git branches created
- [x] Coordination system ready
- [x] All changes pushed to remote
- [ ] **START HERE**: Build components with Copilot (Tasks 1.5-1.7)

### During Component Building
- [ ] Run sync-check.sh every 4 hours
- [ ] Monitor task-assignments.json for updates
- [ ] Run daily-integration.sh at end of day

### After Phase 1 Complete
- [ ] Merge phase1-integration → main
- [ ] Tag release: `git tag v1.1.0-phase1-complete`
- [ ] Update coordination system for Phase 2
- [ ] Document learnings and improvements

---

## Resources

### Design System
- Design tokens: `frontend/src/app/globals.css`
- Button2 component: `frontend/src/components/ui/Button2.tsx`
- Card2 component: `frontend/src/components/ui/Card2.tsx`
- Demo page: http://localhost:3000/design-system-demo

### Project Docs
- Main TODO: `TODO.md`
- Comprehensive plan: `PLAN.md`
- Architecture: `README.md`
- API endpoints: `backend/API_ENDPOINTS_REPORT.md`

### External Links
- Gemini API docs: https://ai.google.dev/docs
- Copilot docs: https://github.com/features/copilot
- Tailwind CSS: https://tailwindcss.com
- Class Variance Authority: https://cva.style

---

## Support

### Questions?
1. Check `shared/coordination-rules.md`
2. Check `shared/task-partition-plan.md`
3. Review agent-specific instructions (gemini/ or copilot/)
4. Run sync-check.sh for current status

### Issues?
1. Document in `.agents/shared/coordination-issues.log`
2. Run conflict-resolver.sh if conflicts
3. Update coordination rules if new edge case

---

**Status**: ✅ Ready for Component Building  
**Task 1.4**: ✅ Complete (all migrations committed)  
**Next Action**: Start Task 1.5.1 (SkeletonText component)
