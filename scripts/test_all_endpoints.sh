#!/bin/bash
# Test all critical API endpoints

echo "🧪 Testing Career Copilot API Endpoints"
echo "========================================"
echo ""

# Login and get token
echo "📝 Logging in..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"moatasim","password":"moatasim123"}')

TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "Response: $TOKEN_RESPONSE"
  exit 1
fi

echo "✅ Login successful"
echo ""

# Test endpoints
declare -a ENDPOINTS=(
  "GET /api/v1/health:Health Check"
  "GET /api/v1/jobs:Jobs List"
  "GET /api/v1/applications:Applications List"
  "GET /api/v1/analytics/summary:Analytics Summary"
  "GET /api/v1/dashboard/analytics:Dashboard Analytics"
  "GET /api/v1/profile:User Profile"
)

PASSED=0
FAILED=0

for endpoint_info in "${ENDPOINTS[@]}"; do
  IFS=':' read -r endpoint description <<< "$endpoint_info"
  
  method=$(echo $endpoint | cut -d' ' -f1)
  path=$(echo $endpoint | cut -d' ' -f2)
  
  echo "Testing: $description ($endpoint)"
  
  if [ "$path" == "/api/v1/health" ]; then
    # Health endpoint doesn't need auth
    response=$(curl -s -w "\n%{http_code}" http://localhost:8002$path)
  else
    response=$(curl -s -w "\n%{http_code}" -X $method http://localhost:8002$path \
      -H "Authorization: Bearer $TOKEN")
  fi
  
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')
  
  if [ "$http_code" == "200" ]; then
    echo "  ✅ PASSED (HTTP $http_code)"
    ((PASSED++))
  else
    echo "  ❌ FAILED (HTTP $http_code)"
    echo "  Response: $body"
    ((FAILED++))
  fi
  echo ""
done

echo "========================================"
echo "📊 Test Results"
echo "========================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
  echo "🎉 All tests passed!"
  exit 0
else
  echo "⚠️  Some tests failed"
  exit 1
fi
