## TODO List for Fixing Security Issues

### Phase 1: Identification and Assessment

*   [ ] **Task 1.1: Identify affected files**
    *   [ ] [backend] Use `grep` to search for hardcoded passwords (e.g., `password = "..."`, `API_KEY = '...'`).
    *   [ ] [backend] Manually review code sections handling user input for file paths (e.g., `open()`, `os.path.join()`).
    *   [ ] [backend] Search for password hashing implementations (e.g., `hashlib.sha256`, `pbkdf2`).
    *   [ ] [tooling] If available, run SAST tools and analyze reports.
*   [ ] **Task 1.2: Prioritize findings**
    *   [ ] [documentation] Create a prioritized list of identified vulnerabilities with severity levels (Critical, High, Medium, Low).

### Phase 2: Remediation Strategy

*   [ ] **Task 2.1: Hardcoded Passwords**
    *   [ ] [backend] Replace hardcoded passwords with environment variables in development/local environments.
    *   [ ] [backend] Integrate with a secure secrets management system for production environments.
    *   [ ] [config] Update `.env.example` with placeholders for new environment variables.
    *   [ ] [config] Update relevant configuration files to reference environment variables or secret management system.
*   [ ] **Task 2.2: Path Traversal**
    *   [ ] [backend] For each identified vulnerability, implement input sanitization (remove `../`, `..\`, null bytes).
    *   [ ] [backend] For each identified vulnerability, validate expected input format for file paths.
    *   [ ] [backend] For each identified vulnerability, use `os.path.abspath()` and `os.path.join()` with base directory validation.
    *   [ ] [backend] Implement a whitelist of allowed file extensions or directories where applicable.
*   [ ] **Task 2.3: Insufficient Password Hash Computational Effort**
    *   [ ] [backend] Identify and replace weak password hashing algorithms (e.g., MD5, SHA1) with `bcrypt` or `Argon2`.
    *   [ ] [backend] Configure chosen hashing algorithms with sufficiently high work factors.
    *   [ ] [backend] Ensure hash, salt, and algorithm parameters are stored together.

### Phase 3: Verification and Testing

*   [ ] **Task 3.1: Unit and Integration Tests**
    *   [ ] [test] Write new unit tests for hardcoded password fixes (e.g., loading from env vars).
    *   [ ] [test] Write new unit tests for path traversal fixes (e.g., invalid path inputs).
    *   [ ] [test] Write new unit tests for password hash strength.
    *   [ ] [test] Update existing tests to reflect changes.
*   [ ] **Task 3.2: Security Testing**
    *   [ ] [tooling] Re-run SAST tools and verify no new issues are detected.
    *   [ ] [testing] Perform targeted manual security testing (e.g., path traversal attempts, brute-force weak hashes).
    *   [ ] [testing] If applicable, engage security professionals for external penetration testing.
*   [ ] **Task 3.3: Code Review**
    *   [ ] [process] Conduct peer code reviews for all security-related changes.

### Phase 4: Documentation and Best Practices

*   [ ] **Task 4.1: Update Documentation**
    *   [ ] [documentation] Update security sections in `README` or project wiki.
    *   [ ] [documentation] Document the chosen secrets management solution and its usage.
    *   [ ] [documentation] Detail the new password hashing scheme parameters.
*   [ ] **Task 4.2: Establish Guidelines**
    *   [ ] [documentation] Integrate secure coding practices for password management and file handling into development guidelines.
    *   [ ] [process] Provide training or awareness sessions for the development team.
