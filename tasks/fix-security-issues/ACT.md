**Task 1.2: Prioritize findings**

**Prioritized List of Vulnerabilities:**
1.  **High:** Hardcoded secrets in `backend/app/api/v1/slack_integration.py` (`"test-secret"`) and `backend/app/services/integration_service.py` (`"placeholder_token"`).
2.  **High:** MD5 usage across multiple files for various hashing purposes. MD5 is cryptographically broken and should be replaced.
3.  **Medium:** Path traversal potential in `backend/app/api/v1/resume.py` related to `unique_filename` in `os.path.join()`.
4.  **Medium:** PBKDF2 iteration count verification in `backend/app/core/env_manager.py` and `backend/app/utils/security.py`.