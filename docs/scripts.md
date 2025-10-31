# Scripts Quick Reference

This document provides a quick reference to the canonical scripts in the Career Copilot application.

## Database

- **Initialize Database:** `python scripts/database/initialize_database.py`
  - Initializes the database, creating all tables.
  - Optional flags:
    - `--seed`: Seed the database with sample data.
    - `--reset`: Reset the database before initializing.

- **Seed Database:** `python scripts/database/seed.py`
  - Seeds the database with sample data.
  - Optional flags:
    - `--all`: Seed all data.
    - `--users`: Seed users.
    - `--jobs`: Seed jobs.
    - `--applications`: Seed applications.
    - `--precedents`: Seed precedents.
    - `--force`: Force seeding without confirmation.
    - `--reset`: Reset existing data before seeding.

- **Reset Database:** `python scripts/database/reset_database.py`
  - Drops all tables and recreates the database.

## Verification

- **Frontend Verification:** `bash scripts/verify/frontend.sh`
  - Verifies the frontend code for quality and correctness.
  - Optional flags:
    - `--quick`: Fast checks (TS errors, lint config).
    - `--structural`: File checks, React.memo, JSDoc.
    - `--full`: All checks + run linter/tests.

## Services

- **Celery Worker:** `python backend/scripts/celery/start_celery_worker.py`
  - Starts a Celery worker.

- **Celery Beat:** `python backend/scripts/celery/start_celery_beat.py`
  - Starts the Celery beat scheduler.