## ACT.md Log

### 2025-11-03

- Created directory `tests/custom`.
- Created file `tests/custom/test_resume_upload_error.py`.
- Attempted to fix Pydantic `Config` deprecation warnings in `backend/app/schemas/resume.py`.
- Fixed indentation issues in `backend/app/schemas/resume.py`.
- Renamed Pydantic schemas in `backend/app/schemas/interview.py` to avoid SQLAlchemy conflicts.
- Updated import statements in `backend/app/schemas/__init__.py` to reflect new schema names.
- Updated import statements in `backend/app/api/v1/interview.py` to use new schema names.
- Updated import statements in `backend/app/services/interview_practice_service.py` to use new schema names.
- Reverted all changes related to the test file and schema renaming.
- Updated `start_backend.sh` to include `--reload-dir` for `app` and `config` directories.
- Added `__version__` attribute to `ResumeParserService` in `backend/app/services/resume_parser_service.py`.
- Logged `ResumeParserService` version on startup in `backend/app/main.py`.
