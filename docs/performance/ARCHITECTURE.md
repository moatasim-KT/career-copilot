# Performance Architecture

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

_Phase 2 · Task 2.1 baseline plan_

Career Copilot now enters the “Enhancements & Optimizations” phase. This page captures how we will identify and remediate performance bottlenecks across the stack.

## Objectives

- Build a repeatable **profiling workflow** for backend APIs, database access, Redis caching, and frontend bundles.
- Capture quantitative baselines before optimizing so we can prove improvements.
- Feed findings back into `TODO.md` / tracking issues so the optimization loop stays visible.

## Backend Profiling Playbook

1. **Spin up services**
	```bash
	docker-compose up -d backend redis postgres
	```
2. **Run the performance suite** (low concurrency first to avoid overwhelming local machines):
	```bash
	python scripts/performance/performance_optimization_suite.py \
	  --backend-url http://localhost:8000 \
	  --users 25 \
	  --requests 5 \
	  --output reports/performance_optimization_report.json
	```
	- Exercises `/api/v1/health`, job listings, recommendations, analytics, and exports while capturing latency, throughput, CPU, and memory stats.
	- Emits slow-query warnings via `DatabaseManager._setup_performance_monitoring` (logs anything >1 s).
3. **Collect slow query samples**
	- Tail `backend/logs/backend.log` for “Slow query on write engine” entries.
	- Hit `/api/v1/database/performance` (FastAPI route) to fetch summarized metrics if the optimizer is enabled.
4. **Index analysis**
	- The suite automatically inspects key tables (users, jobs, analytics) and suggests missing indexes.
	- Track accepted index changes in Alembic migrations so environments stay consistent.
5. **Redis cache validation**
	- `backend/app/core/cache.py` implements specialized caches (e.g., `user_profile_cache`).
	- Use `docker-compose exec redis redis-cli info stats` after the load test to confirm hit ratios and eviction counts.
	- Follow up with `backend/app/tasks/cache_tasks.py` warmers if hit rates are low.

## Database Optimization Checklist

- [ ] Enable `pg_stat_statements` in the Docker Postgres image (if not already) to unlock `EXPLAIN` data.
- [ ] For each slow query log entry:
  1. Capture the full SQL from logs or by enabling `echo=True` temporarily.
  2. Run `EXPLAIN (ANALYZE, BUFFERS)` inside `docker-compose exec postgres psql ...`.
  3. Document findings in `reports/performance/slow-query-YYYYMMDD.md`.
- [ ] Add compound indexes for `jobs(user_id, status)` and similar filters if they appear in the missing-index set.
- [ ] Re-run the performance suite to confirm <100 ms p95 for frequently executed queries.

## Frontend Performance Plan

1. **Production build + audit**
	```bash
	cd frontend
	npm install
	NODE_OPTIONS=--max-old-space-size=4096 npm run build
	node scripts/performance-audit.js
	```
	- Generates `frontend/reports/performance/performance-audit-<date>.md` with bundle analysis.
	- Automatically runs Lighthouse CI (`lighthouserc.json`) and records scores.
2. **Bundle inspection**
	- Investigate any JavaScript chunk >200 KB (reported in the audit).
	- Track remediation tasks (code-splitting, dynamic imports) under Task 2.1.
3. **Core Web Vitals**
	- The script documents LCP/CLS/FID targets. Use `npm run dev` + Chrome DevTools for ad-hoc verification when fixing regressions.

## Reporting & Next Steps

- Store all artifacts under `reports/performance/` (backend) and `frontend/reports/performance/`.
- After each profiling pass, log a short summary in `PROJECT_STATUS.md` and open follow-up TODO items (e.g., “Add index on jobs(status)” or “Lazy load interview practice charts”).
- Upcoming work items:
  1. Capture baseline metrics by running both backend and frontend suites (due next work session).
  2. Prioritize fixes: start with the slowest DB query and the heaviest frontend bundle.
  3. Re-test to confirm improvements and keep iterating until Task 2.1 acceptance criteria are met.
