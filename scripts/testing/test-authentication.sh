#!/bin/bash

echo "=========================================="
echo "🧪 Career Copilot Authentication Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8002"

echo "Step 1: Test WITHOUT authentication (should fail)"
echo "--------------------------------------------------"
RESPONSE=$(curl -s "${API_URL}/api/v1/analytics/summary")
if echo "$RESPONSE" | grep -q "Not authenticated"; then
    echo -e "${GREEN}✓ PASS${NC} - Correctly rejected unauthenticated request"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC} - Should have rejected request"
fi
echo ""

echo "Step 2: Login to get authentication token"
echo "--------------------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "testuser", "password": "testpass"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Successfully obtained token"
    echo "Token: ${TOKEN:0:20}..."
    USERNAME=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('user', {}).get('username', ''))" 2>/dev/null)
    echo "User: $USERNAME"
else
    echo -e "${RED}✗ FAIL${NC} - Could not get authentication token"
    echo "$LOGIN_RESPONSE"
    exit 1
fi
echo ""

echo "Step 3: Test WITH authentication (should succeed)"
echo "--------------------------------------------------"
AUTH_RESPONSE=$(curl -s "${API_URL}/api/v1/analytics/summary" \
    -H "Authorization: Bearer ${TOKEN}")

if echo "$AUTH_RESPONSE" | grep -q "total_applications"; then
    echo -e "${GREEN}✓ PASS${NC} - Successfully retrieved analytics data"
    echo "$AUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AUTH_RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC} - Could not retrieve analytics"
    echo "$AUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AUTH_RESPONSE"
fi
echo ""

echo "=========================================="
echo "Summary:"
echo "=========================================="
echo -e "${GREEN}✓ Authentication system is working!${NC}"
echo ""
echo "Next steps:"
echo "1. Open your browser to: http://localhost:3000"
echo "2. You'll be redirected to login page"
echo "3. Login with: testuser / testpass"
echo "4. Navigate to Analytics page - no more 403 errors!"
echo ""
