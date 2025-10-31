#!/bin/bash

# API Key Rotation Script
# Safely rotate all API keys and secrets

set -e

echo "🔐 Career Copilot - API Key Rotation Script"
echo "==========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo -e "${RED}Error: backend/.env file not found${NC}"
    exit 1
fi

# Backup current .env
BACKUP_FILE="backend/.env.backup.$(date +%Y%m%d_%H%M%S)"
cp backend/.env "$BACKUP_FILE"
echo -e "${GREEN}✓ Backed up current .env to $BACKUP_FILE${NC}"

# Function to generate secure random string
generate_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe($1))"
}

echo ""
echo "📝 Rotating secrets..."
echo ""

# 1. JWT Secret Key
echo "1. Generating new JWT secret key..."
NEW_JWT_SECRET=$(generate_secret 32)
sed -i.tmp "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_JWT_SECRET/" backend/.env
echo -e "${GREEN}✓ JWT secret key rotated${NC}"

# 2. Database Password (if using PostgreSQL)
echo ""
echo "2. Database password rotation"
echo -e "${YELLOW}⚠ Manual action required: Update database password in your database server${NC}"
echo "   Then update DATABASE_URL in .env file"

# 3. OpenAI API Key
echo ""
echo "3. OpenAI API key rotation"
echo -e "${YELLOW}⚠ Manual action required:${NC}"
echo "   1. Go to https://platform.openai.com/api-keys"
echo "   2. Create new API key"
echo "   3. Update OPENAI_API_KEY in .env"
echo "   4. Delete old API key from OpenAI dashboard"

# 4. Anthropic API Key
echo ""
echo "4. Anthropic API key rotation"
echo -e "${YELLOW}⚠ Manual action required:${NC}"
echo "   1. Go to https://console.anthropic.com/settings/keys"
echo "   2. Create new API key"
echo "   3. Update ANTHROPIC_API_KEY in .env"
echo "   4. Delete old API key from Anthropic console"

# 5. Groq API Key
echo ""
echo "5. Groq API key rotation"
echo -e "${YELLOW}⚠ Manual action required:${NC}"
echo "   1. Go to https://console.groq.com/keys"
echo "   2. Create new API key"
echo "   3. Update GROQ_API_KEY in .env"
echo "   4. Delete old API key from Groq console"

# 6. OAuth Secrets
echo ""
echo "6. OAuth client secrets rotation"
echo -e "${YELLOW}⚠ Manual action required:${NC}"
echo "   Google: https://console.cloud.google.com/apis/credentials"
echo "   GitHub: https://github.com/settings/developers"
echo "   LinkedIn: https://www.linkedin.com/developers/apps"

# 7. SMTP Password
echo ""
echo "7. SMTP password rotation"
echo -e "${YELLOW}⚠ Manual action required:${NC}"
echo "   For Gmail: Generate new app password at https://myaccount.google.com/apppasswords"
echo "   Update SMTP_PASSWORD in .env"

# 8. Redis Password
echo ""
echo "8. Redis password rotation"
echo -e "${YELLOW}⚠ Manual action required:${NC}"
echo "   Update Redis server configuration"
echo "   Update REDIS_URL in .env"

# Clean up temp files
rm -f backend/.env.tmp

echo ""
echo "==========================================="
echo -e "${GREEN}✓ Automatic rotations completed${NC}"
echo ""
echo "📋 Next Steps:"
echo "1. Complete manual API key rotations listed above"
echo "2. Update secrets in production environment"
echo "3. Restart application services"
echo "4. Test all integrations"
echo "5. Delete old API keys from provider dashboards"
echo ""
echo "⚠️  Important: Keep backup file secure: $BACKUP_FILE"
echo ""
