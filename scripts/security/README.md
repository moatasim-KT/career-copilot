# Security Scripts

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

Security tools and scripts for Career Copilot.

## Quick Links
- [[../../docs/index|Main Documentation Hub]]
- [[../../frontend/docs/SECURITY_GUIDE.md|Frontend Security Guide]]
- [[../../.github/instructions/snyk_rules.instructions.md|Snyk Security Rules]]
- [[DEVELOPER_GUIDE#security|Security Best Practices]]
- [[../README.md|Scripts Documentation]]

## Scripts

### 1. `check_secrets.py`
Scans repository for exposed secrets and credentials.

```bash
python scripts/security/check_secrets.py
```

**What it checks:**
- AWS access keys
- API keys
- Passwords
- Private keys
- JWT tokens
- OpenAI keys

### 2. `rotate_api_keys.sh`
Safely rotates all API keys and secrets.

```bash
./scripts/security/rotate_api_keys.sh
```

**What it does:**
- Backs up current .env file
- Generates new JWT secret
- Provides instructions for manual key rotation
- Lists all keys that need rotation

### 3. `security_audit.py`
Comprehensive security audit of the entire codebase.

```bash
python scripts/security/security_audit.py
```

**What it checks:**
- Exposed secrets
- Python dependency vulnerabilities
- Security issues with Bandit
- .gitignore configuration
- Environment file tracking
- Hardcoded credentials

## Setup

Install security tools:

```bash
pip install -r scripts/security/requirements.txt
```

## Usage

### Quick Security Check

```bash
# Check for secrets
python scripts/security/check_secrets.py

# Run full audit
python scripts/security/security_audit.py
```

### Rotate API Keys

```bash
# Rotate all keys
./scripts/security/rotate_api_keys.sh

# Follow manual instructions for external services
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/security.yml
- name: Security Audit
  run: |
    pip install -r scripts/security/requirements.txt
    python scripts/security/security_audit.py
```

## Best Practices

1. **Never commit secrets**
   - Use `.env` files (gitignored)
   - Use environment variables
   - Use secrets management services

2. **Rotate keys regularly**
   - Every 90 days minimum
   - Immediately after exposure
   - After team member departure

3. **Run security checks**
   - Before every commit (pre-commit hook)
   - In CI/CD pipeline
   - Weekly scheduled scans

4. **Monitor and respond**
   - Set up alerts for security issues
   - Have incident response plan
   - Keep audit logs

## Security Tools

### Recommended Tools

1. **Dependency Scanning**
   - `safety` - Python vulnerabilities
   - `npm audit` - Node.js vulnerabilities
   - Snyk - Multi-language scanning

2. **Code Analysis**
   - `bandit` - Python security linter
   - `semgrep` - Pattern-based analysis
   - SonarQube - Comprehensive analysis

3. **Secrets Detection**
   - `detect-secrets` - Pre-commit hook
   - `truffleHog` - Git history scanning
   - `git-secrets` - AWS secrets prevention

4. **Penetration Testing**
   - OWASP ZAP - Web app scanner
   - Burp Suite - Security testing
   - Metasploit - Exploitation framework

## Incident Response

If secrets are exposed:

1. **Immediate Actions**
   ```bash
   # Rotate exposed credentials
   ./scripts/security/rotate_api_keys.sh
   
   # Remove from git history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch PATH_TO_FILE" \
     --prune-empty --tag-name-filter cat -- --all
   ```

2. **Verify Removal**
   ```bash
   # Check git history
   git log --all --full-history -- "*.env"
   
   # Scan for secrets
   python scripts/security/check_secrets.py
   ```

3. **Update Services**
   - Revoke old credentials
   - Update production environment
   - Restart services
   - Monitor for unauthorized access

## Contact

For security issues: security@career-copilot.com
