# Frontend Production Readiness TODO List

This TODO list breaks down the plan for making the frontend production-ready.

## Phase 1: CI/CD, Sentry, and Environment (Parallelizable)

- [x] **CI/CD Pipeline Setup** `[ci-cd]` `[github-actions]`
  - [x] Create `.github/workflows/frontend-ci.yml`
  - [x] Configure the workflow to trigger on `push` and `pull_request` for `main` and `develop` branches, targeting `frontend/` paths.
  - [x] Define the `lint-and-format` job:
    - [x] Add steps to checkout code, set up Node.js, install dependencies, and run `npm run quality:check`.
  - [x] Define the `test` job:
    - [x] Add steps to checkout code, set up Node.js, install dependencies, and run `npm test`.
  - [x] Define the `build` job:
    - [x] Add steps to checkout code, set up Node.js, install dependencies, and run `npm run build`.

- [x] **Sentry Integration for Error Monitoring** `[monitoring]` `[frontend]`
  - [x] Install Sentry SDK: `npm install @sentry/nextjs` in the `frontend` directory.
  - [x] Configure Sentry using the wizard: `npx @sentry/wizard@latest -i nextjs`.
  - [x] Verify the creation of `sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`, and `sentry.properties`.
  - [x] Verify `next.config.js` is updated with Sentry configuration.
  - [x] Update Content Security Policy (CSP) in `frontend/src/middleware/csp.ts` to include Sentry domains.

- [x] **Environment Management** `[configuration]` `[frontend]`
  - [x] Create `frontend/.env.example` file.
  - [x] Document required environment variables like `NEXT_PUBLIC_API_URL` and `SENTRY_DSN` in the `.env.example` file.

## Phase 2: Documentation (Parallelizable with Phase 1)

- [x] **Production Readiness Documentation** `[documentation]`
  - [x] Create `docs/deployment/PRODUCTION_CHECKLIST.md`.
    - [x] Add a checklist for pre-deployment steps.
  - [x] Create `docs/troubleshooting/RUNBOOK.md`.
    - [x] Add sections for common issues and their resolutions.
  - [x] Update `docs/deployment/README.md` with a rollback procedure.
