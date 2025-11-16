# Testing Strategies

Career Copilot relies on multiple layers of automated testing to keep the FastAPI + Next.js stack stable. Use this guide as the canonical reference for which suites to run, how to write new tests, and how we keep accessibility checks in CI.

## 🔺 Testing Pyramid

| Layer | Scope | Primary Tools | Typical Commands |
| --- | --- | --- | --- |
| Unit | Pure logic (services, hooks, components) | `pytest`, `jest` | `pytest backend/tests/unit`, `npm run test` |
| Integration | Service boundaries (DB, Celery, API routes) | `pytest` with fixtures, Playwright mocks | `pytest backend/tests/integration`, `npm run test -- <path>` |
| End-to-End | User flows (browser + API) | Playwright | `npm run test:e2e` |
| Non-Functional | Accessibility, performance, security | `jest-axe`, Lighthouse, `make quality-check` | `npm run test:a11y`, `npm run lighthouse`, `make quality-check` |

## 🚀 Quick Commands

```bash
# Full quality sweep (lint + types + security)
make quality-check

# All tests (backend pytest + frontend coverage + a11y)
make test

# Backend only
cd backend && pytest -v

# Frontend coverage-only run (Jest)
cd frontend && npm run test:coverage

# Frontend accessibility regression suite (jest-axe)
cd frontend && npm run test:a11y

# Playwright E2E
cd frontend && npm run test:e2e
```

> **Tip:** `make test-frontend` (called by `make test`) now runs **both** `npm run test:coverage` and `npm run test:a11y`, so CI will fail if accessibility regressions are introduced.

## 🐍 Backend Testing

### Unit Tests (Pytest)
- Location: `backend/tests/unit/`
- Targets pure services (`job_service`, `notification_service`, etc.) and helpers.
- Use dependency-injected fixtures from `backend/tests/conftest.py` to get DB sessions, Celery stubs, and warning filters.
- Example:
	```bash
	cd backend
	pytest tests/unit/test_job_service_ingestion.py -vv
	```

### Integration Tests
- Location: `backend/tests/integration/` + top-level `backend/tests/test_*.py`.
- Spin up the in-memory SQLite DB or the Docker stack (via `docker-compose up backend db redis`) depending on fixture.
- Exercise real API routes, schedulers, scraping harnesses, etc.

### Coverage & Reporting
- Use `pytest -v --cov=backend --cov-report=term-missing` locally for targeted cells.
- CI uses `make test` so coverage deltas are already enforced for merge gates.

## ⚛️ Frontend Testing

### Jest Unit/Component Tests
- Location: `frontend/src/**/__tests__/**/*.test.ts(x)`
- Config: `frontend/.tools/jest.config.js` (Next.js aware) with global setup at `.tools/jest.setup.js`.
- Run `npm test` for all suites or `npm run test -- <pattern>` to scope to a component (e.g., `Badge.a11y.test.tsx`).

### Accessibility Regression Tests (jest-axe)
- Command: `npm run test:a11y`
- Lives alongside component specs (e.g., `src/components/ui/__tests__/ApplicationCard.a11y.test.tsx`, `Badge.a11y.test.tsx`).
- Matchers are registered via `jest-axe/extend-expect` inside `.tools/jest.setup.js`.
- When writing a new a11y test:
	1. Render your component with realistic props using Testing Library.
	2. Call `const results = await axe(container);`.
	3. Assert `expect(results).toHaveNoViolations();` and add targeted ARIA expectations (e.g., `expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite')`).
- **Best practices:**
	- Cover all visual variants (see `Button2.a11y.test.tsx`).
	- Include edge cases like "no interactive props" to ensure defaults remain compliant.
	- If axe flags a violation, fix the component (e.g., add `aria-label`s) before updating the test.

### Playwright E2E Tests
- Location: `frontend/tests/e2e/`
- Run via `npm run test:e2e` (headless) or `npm run test:e2e:ui` for interactive debugging.
- Requires the full stack running (`docker-compose up -d` or manual backend/frontend servers) because the tests hit real APIs.

### Performance & Lighthouse
- Scripts under `frontend/scripts/` assist with bundle audits (`npm run bundle:check`), Lighthouse (`npm run lighthouse`), and custom performance suites (`npm run performance:audit`). Run these before large UI releases or when touching animation-heavy areas.

## ♿ Accessibility Workflow

1. **During Development:**
	 - Add ARIA attributes, keyboard traps, and `aria-hidden` markers directly in components like `Button2` or `Badge`.
	 - Reuse helper props (e.g., `Badge` accepts `role`, `aria-live`, etc.) to avoid one-off wrappers.

2. **Automated Safeguards:**
	 - `npm run test:a11y` is required locally and in CI (via `make test-frontend`).
	 - New components must include at least one axe test that verifies successful rendering and semantic behavior.

3. **Manual Spot Checks:**
	 - Use browser dev tools (`⌘+Option+U` → Lighthouse → Accessibility tab) for UI that is hard to exercise in Jest (drag/drop, modals staggering).
	 - Track issues in `TODO.md` under "Experience & Accessibility Enhancements".

## 🛡️ Security & Dependency Scans

- Run `make security` locally or in CI to execute:
	- `bandit` (Python SAST)
	- `safety` (Python dependency CVEs, JSON under `reports/safety-report.json`)
	- `pip-audit` (Python dependency audit, JSON under `reports/pip_audit_report.json`)
	- `semgrep --config=p/ci` (multi-language SAST, JSON under `reports/semgrep-report.json`)
	- `npm audit --audit-level=high --omit=dev` (frontend dependency scan, JSON under `reports/npm_audit_report.json`)
- Install the dev extras (`pip install -e .[dev,ai,all]`) to get Bandit/Safety/pip-audit and use `pipx install semgrep` (or install it in a virtualenv) so all steps emit reports locally. The Makefile will still succeed without Semgrep, but CI should fail future merges once findings are triaged.
- Authentication defaults to bearer tokens now—set `DISABLE_AUTH=true` in local `.env` files or pytest runs when you need an auth-free environment, and flip it to `false` (the default) in staging/production to enforce JWT + RBAC policies.
- Consume the generated JSON artifacts in CI, or upload them to security dashboards for tracking.

## ✅ Pre-Commit Checklist

Before opening a PR or merging:

- [ ] `make quality-check` (lint, type-check, security)
- [ ] `make test` (backend pytest + frontend coverage + a11y)
- [ ] Add/updated docs (README, `docs/development/testing-strategies.md`, component READMEs) for any new workflows or commands.
- [ ] Optional: `npm run test:e2e` if the change touches authentication, onboarding, or the job/application flows.

Following this guide keeps our split backend/frontend architecture safe, ensures accessibility regressions are caught immediately, and gives future contributors a single source of truth for testing expectations.
