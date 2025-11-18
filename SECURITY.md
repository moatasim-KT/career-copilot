# Security Policy

## Overview

Career Copilot is a self-hosted job application tracking and career management platform designed for **personal use**. While the application implements industry-standard security practices, it is **not currently hardened for public multi-user deployment** without additional security measures.

## Supported Versions

| Version | Supported          | Notes                             |
| ------- | ------------------ | --------------------------------- |
| 1.0.x   | :white_check_mark: | Current stable version            |
| < 1.0   | :x:                | Beta versions no longer supported |

## Security Posture

### Current Security Features ✅

- **Password Hashing**: bcrypt with automatic salting
- **JWT Authentication**: Signed tokens with expiration
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Configurable allowed origins
- **CSP Headers**: Content Security Policy to prevent XSS
- **HTTPS Support**: TLS/SSL ready for production deployment
- **Input Validation**: Pydantic schemas for API validation
- **OAuth Security**: Secure Google/Outlook calendar integration

### Known Security Considerations ⚠️

**For Personal/Single-User Use**: Current security posture is **acceptable**.

**For Public Multi-User Deployment**: The following **high-priority items must be addressed**:

1. **No Rate Limiting** (🔴 CRITICAL)
   - Login endpoints vulnerable to brute force attacks
   - **Mitigation Required**: Implement rate limiting with SlowAPI or similar
   
2. **No Token Revocation** (🟡 HIGH)
   - Logout doesn't invalidate JWT tokens
   - **Mitigation Required**: Implement token blacklist using Redis

3. **OAuth Tokens in Plaintext** (🟡 MEDIUM)
   - Calendar OAuth tokens stored unencrypted in database
   - **Mitigation Required**: Encrypt tokens at application level (Fernet/AES-256)

4. **No CSRF Protection** (🟡 MEDIUM)
   - State-changing endpoints lack CSRF tokens
   - **Mitigation Required**: Add CSRF middleware

For a comprehensive security assessment, see: [`docs/SECURITY_AUDIT_PHASE3.md`](docs/SECURITY_AUDIT_PHASE3.md)

## Reporting a Vulnerability

### For Security Issues

If you discover a security vulnerability in Career Copilot, please report it responsibly:

**📧 Email**: security@career-copilot.com *(or open a private security advisory on GitHub)*

**Please do NOT**:
- Create a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it's fixed
- Test vulnerabilities on production systems without permission

### What to Include

Please provide:

1. **Description**: Clear explanation of the vulnerability
2. **Steps to Reproduce**: Detailed reproduction steps
3. **Impact Assessment**: Potential impact and affected versions
4. **Proof of Concept**: Code or screenshots (if applicable)
5. **Suggested Fix**: Remediation recommendations (optional)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix Timeline**: Varies by severity
  - Critical: 1-2 weeks
  - High: 2-4 weeks
  - Medium: 1-2 months
  - Low: Best effort

### Disclosure Policy

- We follow **coordinated disclosure**
- Vulnerabilities will be disclosed publicly **only after** a fix is released
- Reporter will be credited (unless anonymity is requested)

## Security Best Practices for Deployment

### For Personal Use

1. **Change Default Credentials**
   ```bash
   # backend/.env
   DEFAULT_USER_PASSWORD=your-strong-password-here
   ```

2. **Use Strong JWT Secret**
   ```bash
   # Generate a strong secret
   openssl rand -hex 32
   
   # backend/.env
   JWT_SECRET_KEY=your-generated-secret-here
   ```

3. **Enable HTTPS**
   - Use reverse proxy (Nginx, Caddy) with Let's Encrypt
   - Set `SECURE_COOKIES=true` in production

4. **Keep Dependencies Updated**
   ```bash
   # Backend
   cd backend && pip install -U -r requirements.txt
   
   # Frontend
   cd frontend && npm update
   ```

### For Public Deployment (Additional Requirements)

5. **Implement Rate Limiting**
   - Install SlowAPI: `pip install slowapi`
   - Configure rate limits on authentication endpoints
   - See: `docs/SECURITY_AUDIT_PHASE3.md` Section 1.3

6. **Encrypt OAuth Tokens**
   - Implement token encryption at application level
   - Store encryption key in secure secrets manager
   - See: `docs/SECURITY_AUDIT_PHASE3.md` Section 4.1

7. **Enable Token Revocation**
   - Set up Redis for token blacklist
   - Implement logout token invalidation
   - See: `docs/SECURITY_AUDIT_PHASE3.md` Section 1.2

8. **Restrict CORS Origins**
   ```bash
   # backend/.env
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

9. **Add CSRF Protection**
   - Enable CSRF middleware for state-changing operations
   - Use double-submit cookie pattern
   - See: `docs/SECURITY_AUDIT_PHASE3.md` Section 9

10. **Run Security Scans**
    ```bash
    # Dependency vulnerabilities
    cd backend && pip install snyk && snyk test
    cd frontend && npm audit
    
    # Code security
    cd backend && bandit -r app/
    ```

## Security Update Policy

### Security Patches

- **Critical vulnerabilities**: Hotfix release within 1-2 weeks
- **High vulnerabilities**: Patch release within 2-4 weeks
- **Medium/Low vulnerabilities**: Included in next minor/major release

### Notification Channels

- **GitHub Security Advisories**: Subscribe to repository security updates
- **GitHub Releases**: Security patches tagged as `security` in release notes
- **Changelog**: Security fixes documented in `CHANGELOG.md`

## Security Checklist

Before deploying Career Copilot to production, verify:

- [ ] Changed `DEFAULT_USER_PASSWORD` from default value
- [ ] Generated and set strong `JWT_SECRET_KEY` (32+ characters)
- [ ] Configured `CORS_ORIGINS` to production domain(s)
- [ ] Enabled HTTPS/TLS (no HTTP in production)
- [ ] Set `ENVIRONMENT=production` in backend `.env`
- [ ] Set `NODE_ENV=production` for frontend
- [ ] Reviewed and applied security recommendations from audit
- [ ] Ran `npm audit` and `snyk test` (fixed HIGH/CRITICAL issues)
- [ ] Set up database backups and disaster recovery
- [ ] Configured firewall rules (only ports 80, 443, SSH open)
- [ ] Enabled database encryption at rest (if available)
- [ ] Set up security monitoring and alerting
- [ ] Documented incident response procedures

## Security Resources

### Internal Documentation

- **Comprehensive Security Audit**: [`docs/SECURITY_AUDIT_PHASE3.md`](docs/SECURITY_AUDIT_PHASE3.md)
- **Developer Guide**: [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md)
- **Deployment Guide**: [`docs/deployment/DEPLOYMENT_GUIDE.md`](docs/deployment/DEPLOYMENT_GUIDE.md)

### External Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **Next.js Security**: https://nextjs.org/docs/advanced-features/security-headers
- **PostgreSQL Security**: https://www.postgresql.org/docs/current/security.html

## License

This security policy is part of the Career Copilot project, licensed under the MIT License.

---

**Last Updated**: November 17, 2025  
**Next Review**: Before public deployment or every 6 months
