# Migration Guide

This guide provides instructions for migrating from the old, duplicated scripts to the new, consolidated codebase.

## Migration Checklist

### Pre-Consolidation

- [ ] Create feature branch: `consolidation/duplicate-scripts`
- [ ] Backup current state (git tag: `pre-consolidation`)
- [ ] Run full test suite (establish baseline)
- [ ] Document current import patterns
- [ ] Review report with team
- [ ] Prioritize consolidation efforts
- [ ] Schedule team training session

### Phase 1: Quick Wins

- [ ] Delete backup files
- [ ] Delete test runner backup
- [ ] Remove wrong conftest
- [ ] Add DB init deprecation shims
- [ ] Create canonical verification script
- [ ] Update Celery launchers
- [ ] Update Makefile
- [ ] Update README
- [ ] Create docs/scripts.md
- [ ] Run test suite
- [ ] Deploy to staging
- [ ] Monitor for issues

### Phase 2: Tests

- [ ] Create cache unit tests
- [ ] Create cache integration tests
- [ ] Migrate orchestrators
- [ ] Organize conftest files
- [ ] Update CI pipelines
- [ ] Update test documentation
- [ ] Run full test suite
- [ ] Verify coverage reports

### Phase 3: Services

- [ ] Create unified seeding CLI
- [ ] Implement storage strategy pattern
- [ ] Consolidate config management
- [ ] Organize health checks
- [ ] Update all imports
- [ ] Add deprecation warnings
- [ ] Run integration tests
- [ ] Update service documentation

### Phase 4: Documentation & Cleanup

- [ ] Update all README files
- [ ] Create migration guide
- [ ] Update API documentation
- [ ] Add linter rules for deprecated paths
- [ ] Configure deprecation logging
- [ ] Run full test suite
- [ ] Deploy to staging
- [ ] Monitor for 1 week
- [ ] Deploy to production
- [ ] Monitor for 1 week

### Post-Consolidation

- [ ] Verify no regressions (monitor logs/metrics)
- [ ] Gather team feedback
- [ ] Update onboarding documentation
- [ ] Schedule shim removal (6 months)
- [ ] Create lessons learned document
- [ ] Celebrate success! 🎉

## Import Mapping

| Old Import | New Import |
|---|---|
| `from backend.scripts import init_database` | `from scripts.database import initialize_database` |
| `from backend.scripts import seed_data` | `from scripts.database.seeders import user_seeder` |
| `from backend.app.services import cloud_storage_manager` | `from backend.app.services.storage import storage_manager` |