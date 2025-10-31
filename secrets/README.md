# Secrets Directory

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
