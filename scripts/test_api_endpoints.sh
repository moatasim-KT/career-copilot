#!/bin/bash

# Career Copilot API - Quick Test Script
# Tests core endpoints to verify the API is working

set -e

API_URL="${API_URL:-http://localhost:8000}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Career Copilot API Test Suite"
echo "================================"
echo "Testing API at: $API_URL"
echo ""

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=${4:-200}
    
    echo -n "Testing $description... "
    
    response=$(curl -s -w "\n%{http_code}" -X $method "$API_URL$endpoint" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq "$expected_status" ] || [ "$http_code" -eq 200 ] || [ "$http_code" -eq 307 ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        if [ -n "$body" ] && [ "$body" != "000" ]; then
            echo "  Response: $(echo $body | head -c 100)"
        fi
        return 1
    fi
}

# Track test results
PASSED=0
FAILED=0

# Test Core Endpoints
echo "📍 Core Endpoints"
echo "----------------"

if test_endpoint GET / "Root endpoint"; then ((PASSED++)); else ((FAILED++)); fi
if test_endpoint GET /health "Health check"; then ((PASSED++)); else ((FAILED++)); fi
if test_endpoint GET /metrics "Prometheus metrics"; then ((PASSED++)); else ((FAILED++)); fi

echo ""
echo "🔐 Authentication Endpoints"
echo "---------------------------"

# Authentication endpoints (expect 422 for missing body, which is ok)
if test_endpoint GET /api/v1/auth/oauth/google/login "OAuth Google login" 307; then ((PASSED++)); else ((FAILED++)); fi

echo ""
echo "💼 Jobs Endpoints"
echo "----------------"

if test_endpoint GET /api/v1/jobs "List jobs"; then ((PASSED++)); else ((FAILED++)); fi

echo ""
echo "📝 Applications Endpoints"
echo "-------------------------"

if test_endpoint GET /api/v1/applications "List applications"; then ((PASSED++)); else ((FAILED++)); fi

echo ""
echo "📊 Analytics Endpoints"
echo "---------------------"

if test_endpoint GET /api/v1/analytics/dashboard "Analytics dashboard"; then ((PASSED++)); else ((FAILED++)); fi
if test_endpoint GET /api/v1/analytics/risk-trends "Risk trends"; then ((PASSED++)); else ((FAILED++)); fi

echo ""
echo "🔄 Workflow Endpoints"
echo "--------------------"

if test_endpoint GET /workflows/ "List workflows"; then ((PASSED++)); else ((FAILED++)); fi

echo ""
echo "💾 Database Endpoints"
echo "--------------------"

if test_endpoint GET /api/v1/database-performance/health "Database health"; then ((PASSED++)); else ((FAILED++)); fi
if test_endpoint GET /api/v1/database-performance/metrics "Database metrics"; then ((PASSED++)); else ((FAILED++)); fi

echo ""
echo "🔔 Notification Endpoints"
echo "-------------------------"

if test_endpoint GET /api/v1/notifications/preferences "Notification preferences"; then ((PASSED++)); else ((FAILED++)); fi

echo ""
echo "================================"
echo "📊 Test Summary"
echo "================================"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. View API documentation: open $API_URL/docs"
    echo "  2. Test WebSocket connections"
    echo "  3. Run integration tests"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check the output above for details.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure the backend server is running:"
    echo "     cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo "  2. Check database is running: pg_isready"
    echo "  3. Check Redis is running (optional): redis-cli ping"
    echo "  4. View server logs for errors"
    exit 1
fi
