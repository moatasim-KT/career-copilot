# Task Partition Plan - Phase 1
**Strategy**: File-Level Task Partitioning with Git Branching  
**Goal**: Enable parallel work without conflicts  
**Agents**: Gemini CLI + GitHub Copilot

---

## Overview

This document defines exactly which tasks and files each AI agent will handle during Phase 1 of the Career Copilot frontend upgrade.

### Core Principle
**Different files = Zero conflicts**

- **Gemini CLI**: Modifies existing files (migrations)
- **GitHub Copilot**: Creates new files (components)
- **Result**: No merge conflicts by design

---

## Agent Assignments

### 🤖 Gemini CLI - Migration Specialist

**Branch**: `agent/gemini/phase1-migrations`  
**Status**: Active (currently working)  
**Focus**: Task 1.4 - Migrate existing components to design tokens

#### Assigned Tasks
- ✅ **Task 1.4.1**: Update Button imports in 15 existing files
- ✅ **Task 1.4.2**: Migrate Navigation.tsx to design tokens
- ✅ **Task 1.4.3**: Migrate JobTableView.tsx to design tokens
- ✅ **Task 1.4.4**: Migrate ErrorBoundary.tsx to design tokens
- ✅ **Task 1.4.5**: Migrate NotificationSystem.tsx to design tokens
- ✅ **Task 1.4.6**: Comprehensive sweep for remaining hard-coded colors

#### File Ownership (18 files)
```
frontend/src/components/pages/AdvancedFeaturesPage.tsx
frontend/src/components/pages/RecommendationsPage.tsx
frontend/src/components/pages/JobsPage.tsx
frontend/src/components/pages/ApplicationsPage.tsx
frontend/src/components/pages/JobTableView.tsx
frontend/src/components/common/WebSocketTest.tsx
frontend/src/components/common/ResponsiveDemo.tsx
frontend/src/components/common/ErrorBoundary.tsx
frontend/src/components/layout/Navigation.tsx
frontend/src/components/recommendations/SmartRecommendations.tsx
frontend/src/components/social/SocialFeatures.tsx
frontend/src/components/features/ContentGeneration.tsx
frontend/src/components/features/ResumeUpload.tsx
frontend/src/components/features/InterviewPractice.tsx
frontend/src/components/notifications/NotificationSystem.tsx
frontend/src/components/ui/Modal.stories.tsx
frontend/src/components/ui/Tooltip.stories.tsx
frontend/src/components/ui/EmptyState.stories.tsx
```

#### Work Pattern
1. Modify existing files only (no new files)
2. Replace hard-coded colors with design tokens
3. Update Button → Button2 imports
4. Test in light/dark mode
5. Commit after each subtask

#### Completion Criteria
- All 18 files migrated to design tokens
- All Button imports updated to Button2
- No hard-coded Tailwind colors remain
- Visual regression tests pass

---

### 💬 GitHub Copilot - Component Builder

**Branch**: `agent/copilot/phase1-components`  
**Status**: Waiting for Task 1.4 completion  
**Focus**: Tasks 1.5-1.7 - Build new components

#### Assigned Tasks
- ⏳ **Task 1.5**: Skeleton Loading Components (5 new files)
- ⏳ **Task 1.6**: Input & Form Components (7 new files)
- ⏳ **Task 1.7**: Modal & Dialog System (4 new files)

#### File Ownership (16 NEW files)

**Task 1.5 - Skeleton Components** (5 files)
```
frontend/src/components/common/SkeletonText.tsx (NEW)
frontend/src/components/common/SkeletonCard.tsx (NEW)
frontend/src/components/common/SkeletonAvatar.tsx (NEW)
frontend/src/components/common/SkeletonTable.tsx (NEW)
frontend/src/components/common/Skeleton.tsx (UPDATE + NEW VARIANTS)
```

**Task 1.6 - Input Components** (7 files)
```
frontend/src/components/ui/Input.tsx (NEW)
frontend/src/components/ui/Select.tsx (NEW)
frontend/src/components/ui/MultiSelect.tsx (NEW)
frontend/src/components/ui/DatePicker.tsx (NEW)
frontend/src/components/ui/FileUpload.tsx (NEW)
frontend/src/components/ui/PasswordInput.tsx (NEW)
frontend/src/components/ui/Textarea.tsx (NEW)
```

**Task 1.7 - Modal System** (4 files)
```
frontend/src/components/ui/Modal.tsx (NEW VERSION)
frontend/src/components/ui/Dialog.tsx (NEW)
frontend/src/components/ui/Popover.tsx (NEW)
frontend/src/components/ui/Dropdown.tsx (NEW)
```

#### Work Pattern
1. Create new files only (no modifications to existing files)
2. Use design tokens from globals.css
3. Import Button2 and Card2 (not old Button)
4. Follow enterprise patterns (variants, sizes, accessibility)
5. Include prop-types, JSDoc, accessibility features
6. Create matching .stories.tsx file for each component
7. Commit after each component

#### Completion Criteria
- All 16 components built with full functionality
- Storybook stories created for each
- Full TypeScript typing with prop interfaces
- Accessibility features (ARIA, keyboard nav)
- Comprehensive variants and sizes
- Integration tests pass

---

## Timeline & Coordination

### Phase 1: Task 1.4 (Gemini - ✅ COMPLETE)
**Duration**: Completed  
**Deliverable**: ✅ 18 migrated files (all committed)

```
[x] 1.4.1 - Button import updates (15 files)
[x] 1.4.2 - Navigation migration
[x] 1.4.3 - JobTableView migration
[x] 1.4.4 - ErrorBoundary migration
[x] 1.4.5 - NotificationSystem migration
[x] 1.4.6 - Comprehensive sweep
```

**Status**: All changes committed to main branch

---

### Phase 2: Tasks 1.5-1.7 (Copilot - 🚀 ACTIVE NOW)
**Duration**: ~8-10 hours (START NOW)  
**Deliverable**: 16 new components + Storybook stories

```
[ ] 1.5 - Skeleton components (5 files) - 3 hours ← START HERE
[ ] 1.6 - Input components (7 files) - 4 hours
[ ] 1.7 - Modal system (4 files) - 3 hours
```

**Gemini Status**: ✅ Task 1.4 complete - Idle (available for Phase 2+ tasks)

---

### Phase 3: Tasks 1.8-1.10 (Both Agents - BLOCKED)
**Status**: Wait for components to complete  
**Tasks**:
- 1.8: Storybook integration (NEEDS 1.5-1.7 done)
- 1.9: Form builders (NEEDS 1.6 done)
- 1.10: Accessibility audit (NEEDS all components)

---

## Conflict Prevention Rules

### 🚫 Prohibited Actions

**Gemini CLI CANNOT**:
- Create new component files
- Modify files in Tasks 1.5-1.7
- Work on Storybook configurations

**GitHub Copilot CANNOT**:
- Modify files from Task 1.4
- Touch existing components (Navigation, JobTableView, etc.)
- Update Button imports in old files

### ✅ Safe Actions

**Gemini CLI CAN**:
- Modify any of the 18 assigned files
- Update imports in existing files
- Replace hard-coded colors
- Fix bugs in migrated components

**GitHub Copilot CAN**:
- Create any new component file
- Add Storybook stories
- Create test files
- Add documentation

---

## Daily Workflow

### Morning Sync (9 AM)
1. Run `sync-check.sh` to verify status
2. Check `task-assignments.json` for updates
3. Review overnight progress

### During Work
- Update `task-assignments.json` when starting new task
- Commit frequently (after each file/component)
- Use conventional commit messages

### End of Day (6 PM)
1. Run `daily-integration.sh` to merge branches
2. Run integration tests
3. Update `task-assignments.json` with completed tasks
4. Document any issues in coordination-issues.log

---

## Communication Protocol

### Status Updates
Update `task-assignments.json` immediately when:
- Starting a new task
- Completing a task
- Encountering a blocker
- Finishing for the day

### Format
```json
{
  "agents": {
    "gemini": {
      "status": "active",
      "current_task": "1.4.3",
      "assigned_files": ["frontend/src/components/pages/JobTableView.tsx"],
      "completed_tasks": ["1.4.1", "1.4.2"]
    }
  }
}
```

---

## Success Metrics

### Conflict Rate
**Target**: 0 conflicts  
**Current**: 0 (by design)

### Completion Rate
**Task 1.4** (Gemini): 0/6 subtasks (0%)  
**Tasks 1.5-1.7** (Copilot): Waiting

### Integration Health
**Daily builds**: Target 100% pass rate  
**Test coverage**: Maintain >80%

---

## Emergency Procedures

### If Conflict Occurs
1. Stop both agents immediately
2. Run `conflict-resolver.sh`
3. Identify which agent should own the file
4. Revert incorrect changes
5. Update coordination rules

### If Agent Gets Blocked
1. Update status in `task-assignments.json`
2. Document blocker in GitHub issue
3. Assign task to other agent if possible
4. Continue with non-blocked tasks

---

## Next Steps

### Immediate (Task 1.4 Already Complete ✅)
1. [x] Task 1.4 subtasks complete and committed
2. [x] Gemini status set to "idle" in task-assignments.json
3. [x] Git branches created and pushed:
   - `agent/gemini/phase1-migrations` (Gemini's completed work)
   - `agent/copilot/phase1-components` (Copilot's current work)
4. [x] Copilot status set to "active"
5. [ ] **START NOW**: Task 1.5.1 (SkeletonText component)

### Short Term (Next 3-4 Days)
- Complete Tasks 1.5-1.7 (Copilot)
- Daily integration merges
- Run sync checks every 4 hours

### Medium Term (Phase 2+)
- Expand coordination to Phases 2-6
- Add more agents if needed (e.g., Claude CLI for testing)
- Refine task partitioning based on learnings

---

**Last Updated**: November 8, 2025  
**Status**: ✅ Task 1.4 Complete - Ready for Component Building  
**Next Action**: Start Task 1.5.1 (SkeletonText)
