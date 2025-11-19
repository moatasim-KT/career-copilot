# Secrets Directory

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

⚠️ **SECURITY WARNING**: This directory contains sensitive credentials and should NEVER be committed to git.

## Files in this directory (excluded from git):
- `db_password.txt` - Database password
- `groq_api_key.txt` - Groq AI API key
- `jwt_secret.txt` - JWT secret key for authentication
- `openai_api_key.txt` - OpenAI API key
- `ssl/` - SSL certificates and private keys

## Setup Instructions:

1. Copy the template files from `config/templates/secrets.template.yaml`
2. Fill in your actual credentials
3. These files are automatically ignored by git

## Security Best Practices:
- Never commit actual secrets to version control
- Use environment variables in production
- Rotate keys regularly
- Use different keys for development/staging/production
