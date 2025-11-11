# Security Guide

This guide provides comprehensive security guidelines and best practices for the Career Copilot application.

## Table of Contents

- [Overview](#overview)
- [Security Principles](#security-principles)
- [Authentication & Authorization](#authentication--authorization)
- [XSS Prevention](#xss-prevention)
- [CSRF Protection](#csrf-protection)
- [Input Validation](#input-validation)
- [API Security](#api-security)
- [Data Protection](#data-protection)
- [Dependency Security](#dependency-security)
- [Security Headers](#security-headers)
- [Environment Variables](#environment-variables)
- [Security Testing](#security-testing)
- [Incident Response](#incident-response)

## Overview

Security is a critical aspect of the Career Copilot application. This guide outlines security measures, best practices, and procedures to protect user data and prevent common vulnerabilities.

### Security Audit

Run the automated security audit:

```bash
cd frontend
npm run security:audit
```

This will check for:
- Dependency vulnerabilities (npm audit)
- XSS vulnerabilities
- CSRF protection
- Authentication security
- API security
- Environment variable handling
- Exposed secrets

## Security Principles

### Defense in Depth

Implement multiple layers of security:
1. **Client-side validation** - First line of defense
2. **Server-side validation** - Never trust client input
3. **Database constraints** - Final validation layer
4. **Monitoring & logging** - Detect and respond to threats

### Principle of Least Privilege

- Grant minimum necessary permissions
- Use role-based access control (RBAC)
- Limit API access based on user roles
- Restrict database access

### Secure by Default

- Enable security features by default
- Require opt-in for less secure options
- Use secure defaults in configuration
- Fail securely (deny access on error)

## Authentication & Authorization

### Password Security

**Requirements:**
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, and symbols
- No common passwords (use password strength library)
- No password reuse

**Storage:**
- Never store passwords in plain text
- Use bcrypt or Argon2 for hashing (backend)
- Use high cost factor (10-12 for bcrypt)
- Salt passwords automatically

**Example (backend):**

```typescript
import bcrypt from 'bcrypt';

// Hash password
const saltRounds = 12;
const hashedPassword = await bcrypt.hash(password, saltRounds);

// Verify password
const isValid = await bcrypt.compare(password, hashedPassword);
```

### Token Management

**JWT Best Practices:**
- Short expiration time (15-30 minutes)
- Use refresh tokens for long-lived sessions
- Store tokens securely (httpOnly cookies preferred)
- Include user ID and roles in payload
- Sign with strong secret (256-bit minimum)

**Token Storage:**

```typescript
// ❌ BAD: localStorage (vulnerable to XSS)
localStorage.setItem('token', token);

// ✅ GOOD: httpOnly cookie (set by backend)
// Cookie: token=xxx; HttpOnly; Secure; SameSite=Strict
```

**Token Refresh:**

```typescript
// Refresh token before expiration
const refreshToken = async () => {
  const response = await api.post('/auth/refresh', {
    refreshToken: getRefreshToken()
  });
  
  setAccessToken(response.data.accessToken);
};

// Auto-refresh 5 minutes before expiration
useEffect(() => {
  const interval = setInterval(refreshToken, 10 * 60 * 1000);
  return () => clearInterval(interval);
}, []);
```

### Session Management

**Best Practices:**
- Regenerate session ID after login
- Invalidate session on logout
- Implement session timeout (30 minutes inactivity)
- Allow users to view active sessions
- Provide "logout all devices" option

**Session Invalidation:**

```typescript
const logout = async () => {
  // Clear client-side state
  clearTokens();
  clearUserData();
  
  // Invalidate server-side session
  await api.post('/auth/logout');
  
  // Redirect to login
  router.push('/login');
};
```

### Two-Factor Authentication (2FA)

**Implementation:**
- Support TOTP (Time-based One-Time Password)
- Provide backup codes
- Allow SMS as fallback (less secure)
- Require 2FA for sensitive actions

## XSS Prevention

### React's Built-in Protection

React automatically escapes values in JSX:

```tsx
// ✅ SAFE: React escapes the value
<div>{userInput}</div>

// ❌ DANGEROUS: Bypasses React's protection
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

### Sanitizing HTML

When you must render HTML, sanitize it first:

```typescript
import DOMPurify from 'dompurify';

// Sanitize HTML before rendering
const sanitizedHTML = DOMPurify.sanitize(userHTML, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p'],
  ALLOWED_ATTR: ['href']
});

<div dangerouslySetInnerHTML={{ __html: sanitizedHTML }} />
```

### Content Security Policy (CSP)

Configure CSP headers to prevent XSS:

```javascript
// next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' 'unsafe-eval' 'unsafe-inline';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: https:;
      font-src 'self' data:;
      connect-src 'self' https://api.example.com;
      frame-ancestors 'none';
    `.replace(/\s{2,}/g, ' ').trim()
  }
];
```

### Avoiding Dangerous Patterns

```typescript
// ❌ NEVER use eval()
eval(userInput);

// ❌ NEVER use new Function()
new Function(userInput)();

// ❌ NEVER use innerHTML directly
element.innerHTML = userInput;

// ❌ NEVER use document.write()
document.write(userInput);

// ✅ Use safe alternatives
const safeValue = DOMPurify.sanitize(userInput);
```

## CSRF Protection

### CSRF Token Implementation

**Backend generates token:**

```typescript
// Generate CSRF token
const csrfToken = crypto.randomBytes(32).toString('hex');

// Store in session
req.session.csrfToken = csrfToken;

// Send to client
res.cookie('XSRF-TOKEN', csrfToken, {
  httpOnly: false, // Client needs to read it
  secure: true,
  sameSite: 'strict'
});
```

**Frontend includes token:**

```typescript
// Read CSRF token from cookie
const getCsrfToken = () => {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('XSRF-TOKEN='))
    ?.split('=')[1];
};

// Include in requests
axios.interceptors.request.use(config => {
  const token = getCsrfToken();
  if (token) {
    config.headers['X-CSRF-Token'] = token;
  }
  return config;
});
```

### SameSite Cookies

```typescript
// Set SameSite attribute on cookies
res.cookie('session', sessionId, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict', // or 'lax' for some cross-site requests
  maxAge: 24 * 60 * 60 * 1000 // 24 hours
});
```

## Input Validation

### Client-Side Validation

Use Zod for type-safe validation:

```typescript
import { z } from 'zod';

const jobSchema = z.object({
  title: z.string().min(1).max(200),
  company: z.string().min(1).max(200),
  location: z.string().min(1).max(200),
  salary: z.number().positive().optional(),
  url: z.string().url().optional(),
  description: z.string().max(5000).optional(),
});

type JobInput = z.infer<typeof jobSchema>;

// Validate input
const validateJob = (data: unknown): JobInput => {
  return jobSchema.parse(data);
};
```

### Server-Side Validation

**Always validate on the server:**

```typescript
// Backend validation
app.post('/api/jobs', async (req, res) => {
  try {
    // Validate input
    const validatedData = jobSchema.parse(req.body);
    
    // Sanitize strings
    const sanitizedData = {
      ...validatedData,
      title: sanitizeString(validatedData.title),
      company: sanitizeString(validatedData.company),
    };
    
    // Process request
    const job = await createJob(sanitizedData);
    res.json(job);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ errors: error.errors });
    } else {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});
```

### Sanitization

```typescript
import validator from 'validator';

// Sanitize string input
const sanitizeString = (input: string): string => {
  return validator.escape(validator.trim(input));
};

// Sanitize email
const sanitizeEmail = (email: string): string => {
  return validator.normalizeEmail(email) || '';
};

// Sanitize URL
const sanitizeUrl = (url: string): string => {
  return validator.isURL(url) ? url : '';
};
```

## API Security

### Rate Limiting

**Implement rate limiting on all endpoints:**

```typescript
// Backend rate limiting
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', limiter);

// Stricter limit for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // 5 attempts per 15 minutes
  skipSuccessfulRequests: true,
});

app.use('/api/auth/login', authLimiter);
```

### API Authentication

**Require authentication for protected endpoints:**

```typescript
// Middleware to verify JWT
const authenticateToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(403).json({ error: 'Invalid token' });
  }
};

// Protected route
app.get('/api/jobs', authenticateToken, async (req, res) => {
  const jobs = await getJobsForUser(req.user.id);
  res.json(jobs);
});
```

### CORS Configuration

```typescript
// Configure CORS properly
import cors from 'cors';

const corsOptions = {
  origin: process.env.FRONTEND_URL,
  credentials: true,
  optionsSuccessStatus: 200
};

app.use(cors(corsOptions));
```

### Request Size Limits

```typescript
// Limit request body size
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
```

## Data Protection

### Encryption at Rest

**Encrypt sensitive data in database:**

```typescript
import crypto from 'crypto';

const algorithm = 'aes-256-gcm';
const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');

const encrypt = (text: string): string => {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(algorithm, key, iv);
  
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  const authTag = cipher.getAuthTag();
  
  return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
};

const decrypt = (encrypted: string): string => {
  const [ivHex, authTagHex, encryptedText] = encrypted.split(':');
  
  const iv = Buffer.from(ivHex, 'hex');
  const authTag = Buffer.from(authTagHex, 'hex');
  const decipher = crypto.createDecipheriv(algorithm, key, iv);
  
  decipher.setAuthTag(authTag);
  
  let decrypted = decipher.update(encryptedText, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
};
```

### Encryption in Transit

**Always use HTTPS in production:**

```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains'
          }
        ]
      }
    ];
  }
};
```

### Data Minimization

- Only collect necessary data
- Delete data when no longer needed
- Anonymize data when possible
- Implement data retention policies

## Dependency Security

### Regular Audits

```bash
# Check for vulnerabilities
npm audit

# Fix vulnerabilities automatically
npm audit fix

# Fix with breaking changes
npm audit fix --force
```

### Automated Scanning

**GitHub Dependabot:**
- Enable Dependabot alerts
- Enable Dependabot security updates
- Review and merge security PRs promptly

**Snyk:**

```bash
# Install Snyk
npm install -g snyk

# Authenticate
snyk auth

# Test for vulnerabilities
snyk test

# Monitor project
snyk monitor
```

### Dependency Review

- Review dependencies before adding
- Check package popularity and maintenance
- Verify package authenticity
- Use lock files (package-lock.json)
- Keep dependencies up to date

## Security Headers

### Required Headers

Configure in `next.config.js`:

```javascript
const securityHeaders = [
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on'
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=31536000; includeSubDomains'
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin'
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()'
  }
];

module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ];
  },
};
```

## Environment Variables

### Best Practices

1. **Never commit secrets to version control**
   - Add `.env.local` to `.gitignore`
   - Use `.env.example` for documentation

2. **Use environment-specific files**
   - `.env.local` - Local development
   - `.env.development` - Development environment
   - `.env.production` - Production environment

3. **Prefix client-side variables**
   ```bash
   # Server-side only
   DATABASE_URL=postgresql://...
   JWT_SECRET=...
   
   # Client-side (exposed to browser)
   NEXT_PUBLIC_API_URL=https://api.example.com
   ```

4. **Validate environment variables**
   ```typescript
   const requiredEnvVars = [
     'DATABASE_URL',
     'JWT_SECRET',
     'NEXT_PUBLIC_API_URL'
   ];
   
   requiredEnvVars.forEach(varName => {
     if (!process.env[varName]) {
       throw new Error(`Missing required environment variable: ${varName}`);
     }
   });
   ```

### Secrets Management

**For production, use a secrets manager:**
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Google Secret Manager

## Security Testing

### Automated Testing

**Run security audit:**

```bash
npm run security:audit
```

**Run dependency audit:**

```bash
npm audit
```

**Run Snyk scan:**

```bash
snyk test
```

### Manual Testing

**Test for XSS:**
1. Try injecting `<script>alert('XSS')</script>` in all inputs
2. Try `<img src=x onerror=alert('XSS')>`
3. Try `javascript:alert('XSS')` in URL fields

**Test for CSRF:**
1. Create a malicious form on another domain
2. Try to submit requests without CSRF token
3. Verify SameSite cookie attribute

**Test authentication:**
1. Try accessing protected routes without token
2. Try using expired tokens
3. Try using tokens from other users
4. Test password reset flow

**Test authorization:**
1. Try accessing other users' data
2. Try performing actions without permission
3. Test role-based access control

### Penetration Testing

Consider professional penetration testing:
- Annual security audit
- Before major releases
- After significant changes
- Use reputable security firms

## Incident Response

### Preparation

1. **Security Contact**
   - Designate security point of contact
   - Create security@example.com email
   - Document escalation procedures

2. **Incident Response Plan**
   - Define incident severity levels
   - Document response procedures
   - Assign roles and responsibilities
   - Establish communication channels

### Detection

**Monitor for:**
- Failed login attempts
- Unusual API usage patterns
- Error rate spikes
- Slow response times
- Unauthorized access attempts

**Use monitoring tools:**
- Sentry for error tracking
- CloudWatch/DataDog for metrics
- Security Information and Event Management (SIEM)

### Response

**If security incident occurs:**

1. **Contain**
   - Isolate affected systems
   - Revoke compromised credentials
   - Block malicious IPs

2. **Investigate**
   - Review logs
   - Identify attack vector
   - Assess damage

3. **Remediate**
   - Fix vulnerability
   - Deploy patch
   - Verify fix

4. **Communicate**
   - Notify affected users
   - Report to authorities if required
   - Document incident

5. **Learn**
   - Conduct post-mortem
   - Update security measures
   - Improve monitoring

## Security Checklist

### Development

- [ ] Use HTTPS in production
- [ ] Implement authentication and authorization
- [ ] Validate all user inputs
- [ ] Sanitize data before rendering
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Implement CSRF protection
- [ ] Set security headers
- [ ] Use secure session management
- [ ] Encrypt sensitive data
- [ ] Implement rate limiting
- [ ] Log security events
- [ ] Handle errors securely (don't expose stack traces)

### Deployment

- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Implement backup and recovery
- [ ] Use least privilege for service accounts
- [ ] Keep dependencies up to date
- [ ] Run security scans
- [ ] Review and test security measures

### Ongoing

- [ ] Regular security audits
- [ ] Dependency updates
- [ ] Security training for team
- [ ] Monitor security advisories
- [ ] Review access logs
- [ ] Test incident response plan
- [ ] Update security documentation

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Next.js Security](https://nextjs.org/docs/advanced-features/security-headers)
- [React Security](https://react.dev/learn/security)
- [Web Security Academy](https://portswigger.net/web-security)
- [MDN Web Security](https://developer.mozilla.org/en-US/docs/Web/Security)

## Support

For security concerns or to report vulnerabilities:
- Email: security@example.com
- Use responsible disclosure
- Allow reasonable time for fixes
- Do not publicly disclose until patched
