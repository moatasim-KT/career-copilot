# Script duplication audit (repository-wide)

This report inventories maintenance scripts across the repo, clusters them by purpose, highlights overlaps/near-duplicates, and recommends a consolidation plan with minimal disruption.

Last updated: current session

## Scope covered

- Shell scripts: verify, services, setup, Docker entrypoint
- Python scripts under `scripts/**` and `backend/scripts/**`
- Database init/seed/reset, health/verification, Celery worker/beat launchers

## Inventory by category

### A) Verification and quality checks

- Frontend-only
  - `frontend/verify-fixes.sh` – TS compile error count, MSW import deprecation scan, ESLint config presence
- Cross-repo
  - `verify-all-fixes.sh` (root) – file presence/deletion checks; React.memo in `Button`/`Card`; token expiry; JSDoc; sanitization and error types

Overlap assessment

- Theme overlap: “frontend verification” with different assertions. Root script reaches into frontend; frontend script covers compiler/lint/test affordances.
- Risk: drift and partial verification depending on which script is run.

Recommendation

- Canonical: create a single entry `scripts/verify/frontend.sh` that composes all checks (compiler/lint/tests + structural checks) behind flags.
- Keep `frontend/verify-fixes.sh` as a thin wrapper that calls the canonical entry with `--quick` or `--all`.
- Deprecate root `verify-all-fixes.sh` or convert it to call the canonical script with the “structural checks” subset.

### B) Celery worker/beat launchers

- Shell wrappers
  - `scripts/services/celery_worker.sh` → `celery -A app.celery worker ...`
  - `scripts/services/celery_beat.sh` → `celery -A app.celery beat ...`
- Python launchers (backend-aware)
  - `backend/scripts/celery/start_celery_worker.py` – uses `app.core.celery_app.celery_app`, sets queues/hostname
  - `backend/scripts/celery/start_celery_beat.py` – uses app config, specifies schedule/pidfile

Overlap assessment

- Two distinct ways to start the same services; Python variants ensure correct app import/queues; shell wrappers are generic and can miss configuration.

Recommendation

- Canonical: prefer Python launchers for correctness and app-level configuration.
- Keep shell scripts as thin wrappers executing the Python scripts, or remove them to avoid confusion. Standardize invocation via Makefile/Procfile.

### C) Database initialization and reset

- Comprehensive async initializer
  - `scripts/database/initialize_database.py` – creates tables, seeds precedents, optional dev users, runs health validation; supports flags
- Backend initializers (sync)
  - `backend/scripts/init_database.py` – create tables, verify indexes/foreign keys, optional drop/recreate
  - `backend/scripts/simple_db_init.py` – minimal create_all
- Reset
  - `scripts/database/reset_database.py` – drop and recreate all tables

Overlap assessment

- Three initializers with differing depth; functionality overlaps heavily (table creation, optional drop/recreate). The async initializer is feature-complete and aligned with current services.

Recommendation

- Canonical: `scripts/database/initialize_database.py`.
- Deprecate `backend/scripts/init_database.py` and `backend/scripts/simple_db_init.py` (leave wrappers that exec the canonical script to preserve existing docs/links).
- Keep `scripts/database/reset_database.py` as a dedicated “drop + create” tool; optionally re-expose via `initialize_database.py --reset` flag in the future.

### D) Database seeding (vector vs relational)

- Vector/precedents
  - `scripts/database/seed_database.py` – seeds ChromaDB via seeder service, stats, reset flag
  - `scripts/database/seed_precedents.py` – seeds sample precedent clauses directly
- Relational sample data
  - `backend/scripts/seed_data.py` – creates test user/jobs/applications for dev/testing
- Also: `scripts/database/initialize_database.py` can seed precedents and dev users.

Overlap assessment

- Two paths for precedent/vector seeding (service-driven vs inline sample data). Dev-user seeding exists in both the initializer and `backend/scripts/seed_data.py` (the latter also seeds jobs/applications).

Recommendation

- Canonical: expose a single seeding CLI surface under `scripts/database/` with subcommands, e.g. `seed --precedents`, `seed --relational-basic`, `seed --relational-sample-data`.
- Deprecate `seed_precedents.py` in favor of the service-driven `seed_database.py`; fold needed sample entries into the service’s fixtures.
- Move `backend/scripts/seed_data.py` under `scripts/database/seed_relational_sample.py` (or call it from the canonical CLI) to avoid scattering.

### E) Health checks and verification

- Comprehensive health monitor
  - `scripts/database/database_health_monitor.py` – connectivity, performance, backups, migrations, disk, pools, slow queries; JSON/text output; continuous mode
- Targeted backend verifications
  - `backend/scripts/verification/verify_db_connection.py` – quick DB connection/table listing
  - `backend/scripts/verification/verify_migration.py` – SQLite-oriented schema/index verification, inserts/queries sample data
  - `backend/scripts/verification/verify_models.py`, `check_schema.py`, etc.

Overlap assessment

- Multiple “verification” entry points with varying depth/targets. The comprehensive monitor can encompass most checks, but the tiny scripts are useful as quick probes.

Recommendation

- Canonical: keep `database_health_monitor.py` as the primary CI/ops tool. Convert targeted verifications into unit/integration tests where possible, or expose them as subcommands of a single `scripts/verify/backend.py` CLI.
- Tag SQLite-specific scripts clearly or retire if the project standardizes on Postgres.

### F) CI runner, setup, entrypoint

- CI test orchestration
  - `scripts/ci_test_runner.sh` – env setup, run `scripts/test_runner.py`, generate coverage/junit
- Project setup
  - `scripts/setup.sh` – checks runtimes, creates venv, installs backend/frontend deps, runs Alembic
- Container entrypoint
  - `deployment/docker/entrypoint.sh` – readiness checks for DB/Redis, Alembic, optional service init, then exec

Overlap assessment

- Distinct purposes; no duplication beyond standard dev/prod flows.

## Consolidation matrix (high level)

- Verification
  - Keep: one canonical `scripts/verify/frontend.sh` (+ back-compat wrappers)
  - Deprecate/Wrap: `verify-all-fixes.sh` and `frontend/verify-fixes.sh` into canonical
- Celery
  - Keep: Python launchers in `backend/scripts/celery/`
  - Deprecate/Wrap: `scripts/services/celery_worker.sh`, `scripts/services/celery_beat.sh`
- DB Init/Reset
  - Keep: `scripts/database/initialize_database.py`, `scripts/database/reset_database.py`
  - Deprecate/Wrap: `backend/scripts/init_database.py`, `backend/scripts/simple_db_init.py`
- Seeding
  - Keep: `scripts/database/seed_database.py` (as canonical entry) + a unified relational sample seeder
  - Deprecate/Move: `scripts/database/seed_precedents.py`, `backend/scripts/seed_data.py`
- Health/Verification
  - Keep: `scripts/database/database_health_monitor.py`
  - Migrate: targeted verifications into tests or subcommands

## Suggested implementation plan (minimal disruption)

Week 1 (no behavioral change, prep wrappers)

- Add `scripts/verify/frontend.sh` that runs: TypeScript compile, ESLint, tests, and structural checks currently in `verify-all-fixes.sh`.
- Change `frontend/verify-fixes.sh` and `verify-all-fixes.sh` to delegate to the canonical script; mark as deprecated in a header comment.
- Create thin wrappers for `scripts/services/celery_worker.sh` and `scripts/services/celery_beat.sh` that exec their Python counterparts.
- Add a `docs/scripts.md` quick reference with the new “one true path” entries.

Week 2 (move/merge, keep back-compat)

- Move `backend/scripts/seed_data.py` → `scripts/database/seed_relational_sample.py`; update imports if needed; leave a stub in the old path that prints a deprecation notice and calls the new location.
- Merge `seed_precedents.py` content into `seed_database.py` as an optional fixture pack or remove it in favor of the service-driven approach.
- Mark `backend/scripts/init_database.py` and `simple_db_init.py` as deprecated and have them invoke `scripts/database/initialize_database.py` with matching flags.

Week 3 (cleanup once CI/docs updated)

- Update README and any ops runbooks to reference only canonical entries.
- Remove deprecated scripts after a grace period or keep wrappers permanently if external links exist.

## Risks and mitigations

- External automation calling old paths → provide wrapper scripts with clear deprecation messages and exit codes preserved.
- Environment differences (SQLite vs Postgres) → keep SQLite-specific checks as opt-in flags or tests; default canonical flow to Postgres-compatible paths.
- Celery config drift → prefer Python launchers that import app config, ensuring queue/hostname alignment.

## Quick wins adopted immediately (non-breaking)

- Treat Python launchers for Celery as authoritative in docs and Makefile.
- Run `scripts/database/initialize_database.py` for all dev/CI init flows; use `--tables-only` in CI when seeds aren’t needed.
- Prefer `scripts/database/seed_database.py` for vector seeding; avoid calling `seed_precedents.py` directly.

## Appendices

### Files reviewed (representative)

- Shell
  - `frontend/verify-fixes.sh`
  - `verify-all-fixes.sh`
  - `scripts/services/celery_worker.sh`
  - `scripts/services/celery_beat.sh`
  - `scripts/ci_test_runner.sh`
  - `scripts/setup.sh`
  - `deployment/docker/entrypoint.sh`
  - `scripts/security/rotate_api_keys.sh`
- Python (selected)
  - `scripts/test_runner.py`
  - `scripts/database/initialize_database.py`
  - `scripts/database/reset_database.py`
  - `scripts/database/seed_database.py`
  - `scripts/database/seed_precedents.py`
  - `scripts/database/database_health_monitor.py`
  - `backend/scripts/init_database.py`
  - `backend/scripts/simple_db_init.py`
  - `backend/scripts/seed_data.py`
  - `backend/scripts/celery/start_celery_worker.py`
  - `backend/scripts/celery/start_celery_beat.py`
  - `backend/scripts/verification/verify_db_connection.py`
  - `backend/scripts/verification/verify_migration.py`

### Out of scope (no duplication)

- `scripts/ci_test_runner.sh` – CI orchestration
- `scripts/setup.sh` – local bootstrap
- `deployment/docker/entrypoint.sh` – container entrypoint logic
