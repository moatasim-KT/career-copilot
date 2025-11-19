# Environment Configuration Guide

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

## Overview

Career Copilot uses environment variables for configuration to support different deployment environments (development, staging, production) and keep sensitive data secure.

## Environment Files

### Frontend

**Location**: `frontend/.env.local` (create from `frontend/.env.example`)

```bash
# Copy the example file
cp frontend/.env.example frontend/.env.local
```

**Key Variables**:

| Variable                       | Required   | Default                 | Description                    |
| ------------------------------ | ---------- | ----------------------- | ------------------------------ |
| `NEXT_PUBLIC_API_URL`          | ✅ Yes      | `http://localhost:8000` | Backend API base URL           |
| `NEXT_PUBLIC_WS_URL`           | ⚠️ Optional | Derived from API_URL    | WebSocket endpoint URL         |
| `NEXT_PUBLIC_ENV`              | No         | `development`           | Environment mode               |
| `NEXT_PUBLIC_ENABLE_WEBSOCKET` | No         | `true`                  | Enable WebSocket connections   |
| `NEXT_PUBLIC_DEBUG`            | No         | `false`                 | Enable debug logging           |
| `SENTRY_DSN`                   | No         | -                       | Sentry error tracking DSN      |
| `SENTRY_AUTH_TOKEN`            | No         | -                       | Sentry source map upload token |

### Backend

**Location**: `backend/.env` (create from `backend/.env.example`)

```bash
# Copy the example file
cp backend/.env.example backend/.env
```

**Key Variables**:

| Variable         | Required   | Default                  | Description                    |
| ---------------- | ---------- | ------------------------ | ------------------------------ |
| `DATABASE_URL`   | ✅ Yes      | -                        | PostgreSQL connection string   |
| `API_HOST`       | No         | `0.0.0.0`                | API server host                |
| `API_PORT`       | No         | `8000`                   | API server port                |
| `REDIS_URL`      | No         | `redis://localhost:6379` | Redis connection string        |
| `OPENAI_API_KEY` | ⚠️ Optional | -                        | OpenAI API key for AI features |

## Environment-Specific Configuration

### Development

```env
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_ENV=development
NEXT_PUBLIC_DEBUG=true
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
```

```env
# backend/.env
DATABASE_URL=postgresql://user:pass@localhost:5432/career_copilot_dev
API_HOST=0.0.0.0
API_PORT=8000
REDIS_URL=redis://localhost:6379
```

### Staging

```env
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://api.staging.yourapp.com
NEXT_PUBLIC_WS_URL=wss://api.staging.yourapp.com
NEXT_PUBLIC_ENV=staging
NEXT_PUBLIC_DEBUG=false
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

```env
# backend/.env
DATABASE_URL=postgresql://user:pass@db.staging.yourapp.com:5432/career_copilot
API_HOST=0.0.0.0
API_PORT=8000
REDIS_URL=redis://redis.staging.yourapp.com:6379
```

### Production

```env
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXT_PUBLIC_WS_URL=wss://api.yourapp.com
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_DEBUG=false
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
SENTRY_AUTH_TOKEN=your-sentry-auth-token
NEXT_PUBLIC_SENTRY_SAMPLE_RATE=1.0
NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE=0.1
```

```env
# backend/.env
DATABASE_URL=postgresql://user:pass@db.yourapp.com:5432/career_copilot
API_HOST=0.0.0.0
API_PORT=8000
REDIS_URL=redis://redis.yourapp.com:6379
OPENAI_API_KEY=your-openai-api-key
```

## WebSocket Configuration

### Automatic WebSocket URL Derivation

If `NEXT_PUBLIC_WS_URL` is not set, it's automatically derived from `NEXT_PUBLIC_API_URL`:

```typescript
// Automatic conversion
http://localhost:8000 → ws://localhost:8000
https://api.yourapp.com → wss://api.yourapp.com
```

### Manual WebSocket URL

For advanced setups with separate WebSocket servers:

```env
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXT_PUBLIC_WS_URL=wss://ws.yourapp.com  # Different domain
```

## Security Best Practices

### 1. Never Commit `.env` Files

Add to `.gitignore`:
```gitignore
.env
.env.local
.env.*.local
```

### 2. Use Environment-Specific Files

```bash
.env.local           # Local development
.env.development     # Development defaults
.env.staging         # Staging environment
.env.production      # Production environment
```

### 3. Validate Environment Variables

The application validates required environment variables on startup:

```typescript
// frontend/src/lib/config/env.ts
const requiredEnvVars = ['NEXT_PUBLIC_API_URL'];

requiredEnvVars.forEach(varName => {
  if (!process.env[varName]) {
    throw new Error(`Missing required environment variable: ${varName}`);
  }
});
```

### 4. Use Secrets Management

For production:
- **AWS**: AWS Secrets Manager or Parameter Store
- **GCP**: Google Secret Manager
- **Azure**: Azure Key Vault
- **Kubernetes**: Kubernetes Secrets
- **Docker**: Docker Secrets

## Testing Configuration

### Unit Tests

Jest tests use mock values:

```typescript
// jest.setup.js
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
process.env.NEXT_PUBLIC_WS_URL = 'ws://localhost:8000';
```

### E2E Tests

Playwright tests can override via environment:

```bash
PLAYWRIGHT_BASE_URL=http://localhost:3000 npm run test:e2e
```

Or in `playwright.config.js`:

```javascript
use: {
  baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
}
```

## CI/CD Configuration

### GitHub Actions

```yaml
name: Deploy
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up environment
        run: |
          echo "NEXT_PUBLIC_API_URL=${{ secrets.API_URL }}" >> $GITHUB_ENV
          echo "NEXT_PUBLIC_WS_URL=${{ secrets.WS_URL }}" >> $GITHUB_ENV
      
      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.API_URL }}
          SENTRY_DSN: ${{ secrets.SENTRY_DSN }}
```

### Docker

```dockerfile
# Dockerfile
FROM node:18-alpine

# Build-time variables
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL

# Set environment
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

# Build application
RUN npm run build

CMD ["npm", "start"]
```

Build with variables:

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.yourapp.com \
  --build-arg NEXT_PUBLIC_WS_URL=wss://api.yourapp.com \
  -t career-copilot-frontend .
```

## Troubleshooting

### Issue: Environment variables not updating

**Solution**: Restart the development server after changing `.env` files:

```bash
# Stop the server (Ctrl+C)
npm run dev  # Start again
```

### Issue: `NEXT_PUBLIC_*` variables undefined in browser

**Cause**: Variables without `NEXT_PUBLIC_` prefix are only available server-side.

**Solution**: Prefix with `NEXT_PUBLIC_` for browser access:

```env
# ❌ Wrong - not accessible in browser
API_URL=http://localhost:8000

# ✅ Correct - accessible in browser
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Issue: WebSocket connection fails

**Check**:
1. `NEXT_PUBLIC_WS_URL` is set or `NEXT_PUBLIC_API_URL` is correct
2. Backend WebSocket endpoint is running
3. No CORS or firewall issues
4. Protocol matches (`ws://` for HTTP, `wss://` for HTTPS)

**Debug**:
```bash
# Check environment
echo $NEXT_PUBLIC_API_URL
echo $NEXT_PUBLIC_WS_URL

# Test WebSocket
wscat -c ws://localhost:8000/ws
```

### Issue: 401 Unauthorized errors

**Check**:
1. Backend authentication is configured correctly
2. `DISABLE_AUTH` setting matches between frontend and backend
3. No stale tokens in localStorage/cookies

### Issue: API calls go to wrong URL

**Check**:
```typescript
// In browser console
console.log(process.env.NEXT_PUBLIC_API_URL);

// Check compiled code
console.log(API_BASE_URL);  // Should match your .env
```

## Migration from Hardcoded URLs

If you have hardcoded URLs in your code:

### ❌ Before

```typescript
const response = await fetch('http://localhost:8002/api/v1/jobs');
const ws = new WebSocket('ws://localhost:8002/ws');
```

### ✅ After

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

const response = await fetch(`${API_URL}/api/v1/jobs`);
const ws = new WebSocket(`${WS_URL}/ws`);
```

Or use the API client:

```typescript
import { fetchApi } from '@/lib/api/client';

const { data } = await fetchApi('/jobs');  // Automatically uses NEXT_PUBLIC_API_URL
```

## Resources

- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [12-Factor App Config](https://12factor.net/config)
- [Environment Variables Best Practices](https://blog.bitsrc.io/a-guide-to-environment-variables-in-javascript-projects-6c3e4a2c4f9c)
