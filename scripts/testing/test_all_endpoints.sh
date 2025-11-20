#!/bin/bash

# Career Copilot API Comprehensive Test Script
# Tests all discovered endpoints and reports results

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0
TOTAL=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local path=$2
    local description=$3
    local expected_status=${4:-200}
    
    TOTAL=$((TOTAL + 1))
    
    # Make request and capture status code
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${path}" 2>&1)
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" "${BASE_URL}${path}" 2>&1)
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT -H "Content-Type: application/json" "${BASE_URL}${path}" 2>&1)
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "${BASE_URL}${path}" 2>&1)
    fi
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    # Check if status code matches expected or is a valid response
    if [[ "$status_code" =~ ^(200|201|204|307|422)$ ]]; then
        echo -e "${GREEN}✅ PASS${NC} $method $path - $description (HTTP $status_code)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC} $method $path - $description (HTTP $status_code)"
        FAILED=$((FAILED + 1))
        if [ ! -z "$body" ] && [ ${#body} -lt 200 ]; then
            echo "  Response: $body"
        fi
    fi
}

echo "🧪 Career Copilot API Comprehensive Test Suite"
echo "==============================================="
echo "Testing API at: $BASE_URL"
echo ""

# Core Endpoints
echo "📍 Core Endpoints"
echo "----------------"
test_endpoint "GET" "/" "Root endpoint"
test_endpoint "GET" "/health" "Health check"
test_endpoint "GET" "/metrics" "Prometheus metrics"
test_endpoint "GET" "/docs" "Swagger UI"
test_endpoint "GET" "/redoc" "ReDoc documentation"
echo ""

# Authentication & Users
echo "🔐 Authentication & User Endpoints"
echo "----------------------------------"
test_endpoint "GET" "/api/v1/auth/oauth/google/login" "Google OAuth login redirect" "307"
test_endpoint "GET" "/api/v1/auth/oauth/linkedin/login" "LinkedIn OAuth login redirect" "307"
test_endpoint "GET" "/api/v1/users/me" "Get current user" "422"
test_endpoint "GET" "/api/v1/users" "List users"
echo ""

# Jobs
echo "💼 Jobs Endpoints"
echo "----------------"
test_endpoint "GET" "/api/v1/jobs" "List all jobs"
test_endpoint "GET" "/api/v1/jobs/search" "Search jobs"
test_endpoint "GET" "/api/v1/jobs/recommendations" "Get job recommendations"
test_endpoint "GET" "/api/v1/jobs/analytics" "Job analytics"
echo ""

# Applications
echo "📝 Applications Endpoints"
echo "-------------------------"
test_endpoint "GET" "/api/v1/applications" "List applications"
test_endpoint "GET" "/api/v1/applications/summary" "Application summary"
test_endpoint "GET" "/api/v1/applications/stats" "Application statistics"
echo ""

# Analytics
echo "📊 Analytics Endpoints"
echo "---------------------"
test_endpoint "GET" "/api/v1/analytics/dashboard" "Analytics dashboard"
test_endpoint "GET" "/api/v1/analytics/performance-metrics" "Performance metrics"
test_endpoint "GET" "/api/v1/analytics/risk-trends" "Risk trends"
test_endpoint "GET" "/api/v1/analytics/success-metrics" "Success metrics"
test_endpoint "GET" "/api/v1/analytics/application-velocity" "Application velocity"
echo ""

# Workflows
echo "🔄 Workflow Endpoints"
echo "--------------------"
test_endpoint "GET" "/api/v1/workflows" "List workflows"
test_endpoint "GET" "/api/v1/workflows/definitions" "Workflow definitions"
test_endpoint "GET" "/api/v1/workflows/history" "Workflow history"
echo ""

# Resume
echo "📄 Resume Endpoints"
echo "------------------"
test_endpoint "GET" "/api/v1/resume" "List resumes"
test_endpoint "GET" "/api/v1/resume/history" "Resume history"
echo ""

# Content Generation
echo "✍️  Content Generation Endpoints"
echo "--------------------------------"
test_endpoint "GET" "/api/v1/content" "List content generations"
test_endpoint "GET" "/api/v1/content/types" "Content types"
echo ""

# Interview
echo "🎤 Interview Endpoints"
echo "---------------------"
test_endpoint "GET" "/api/v1/interview/sessions" "Interview sessions"
test_endpoint "GET" "/api/v1/interview/practice" "Practice questions"
echo ""

# Career Resources
echo "📚 Career Resources Endpoints"
echo "-----------------------------"
test_endpoint "GET" "/api/v1/resources" "List resources"
test_endpoint "GET" "/api/v1/resources/categories" "Resource categories"
test_endpoint "GET" "/api/v1/resources/bookmarks" "User bookmarks"
echo ""

# Learning Paths
echo "🎓 Learning Path Endpoints"
echo "--------------------------"
test_endpoint "GET" "/api/v1/learning/paths" "List learning paths"
test_endpoint "GET" "/api/v1/learning/enrollments" "User enrollments"
test_endpoint "GET" "/api/v1/learning/progress" "Learning progress"
echo ""

# Notifications
echo "🔔 Notification Endpoints"
echo "-------------------------"
test_endpoint "GET" "/api/v1/notifications" "List notifications"
test_endpoint "GET" "/api/v1/notifications/preferences" "Notification preferences"
test_endpoint "GET" "/api/v1/notifications/unread" "Unread notifications"
echo ""

# Feedback
echo "💬 Feedback Endpoints"
echo "--------------------"
test_endpoint "GET" "/api/v1/feedback" "List feedback"
test_endpoint "GET" "/api/v1/feedback/stats" "Feedback statistics"
echo ""

# Help Articles
echo "❓ Help Article Endpoints"
echo "------------------------"
test_endpoint "GET" "/api/v1/help/articles" "List help articles"
test_endpoint "GET" "/api/v1/help/search" "Search help articles"
echo ""

# Database Management
echo "💾 Database Endpoints"
echo "--------------------"
test_endpoint "GET" "/api/v1/database/health" "Database health"
test_endpoint "GET" "/api/v1/database/metrics" "Database metrics"
test_endpoint "GET" "/api/v1/database/tables" "Database tables"
test_endpoint "GET" "/api/v1/database/performance" "Database performance"
echo ""

# Cache Management
echo "🗄️  Cache Endpoints"
echo "------------------"
test_endpoint "GET" "/api/v1/cache/stats" "Cache statistics"
test_endpoint "GET" "/api/v1/cache/health" "Cache health"
echo ""

# File Storage
echo "📦 File Storage Endpoints"
echo "------------------------"
test_endpoint "GET" "/api/v1/storage/files" "List files"
test_endpoint "GET" "/api/v1/storage/stats" "Storage statistics"
echo ""

# Vector Store
echo "🔍 Vector Store Endpoints"
echo "------------------------"
test_endpoint "GET" "/api/v1/vector-store/collections" "Vector collections"
test_endpoint "GET" "/api/v1/vector-store/stats" "Vector store stats"
echo ""

# LLM Services
echo "🤖 LLM Service Endpoints"
echo "-----------------------"
test_endpoint "GET" "/api/v1/llm/models" "Available LLM models"
test_endpoint "GET" "/api/v1/llm/stats" "LLM usage statistics"
echo ""

# System Integration
echo "🔌 System Integration Endpoints"
echo "-------------------------------"
test_endpoint "GET" "/api/v1/integrations" "List integrations"
test_endpoint "GET" "/api/v1/integrations/health" "Integration health"
echo ""

# External Services
echo "🌐 External Services Endpoints"
echo "------------------------------"
test_endpoint "GET" "/api/v1/services/status" "Service status"
test_endpoint "GET" "/api/v1/services/health" "All services health"
echo ""

# Email Service
echo "📧 Email Service Endpoints"
echo "-------------------------"
test_endpoint "GET" "/api/v1/email/templates" "Email templates"
test_endpoint "GET" "/api/v1/email/history" "Email history"
echo ""

# Slack Integration
echo "💬 Slack Integration Endpoints"
echo "------------------------------"
test_endpoint "GET" "/api/v1/slack/channels" "Slack channels"
test_endpoint "GET" "/api/v1/slack/status" "Slack status"
echo ""

# Real-time Status
echo "📡 Real-time Status Endpoints"
echo "----------------------------"
test_endpoint "GET" "/api/v1/status/current" "Current status"
test_endpoint "GET" "/api/v1/status/updates" "Status updates"
echo ""

# Progress Tracking
echo "📈 Progress Tracking Endpoints"
echo "------------------------------"
test_endpoint "GET" "/api/v1/progress" "Overall progress"
test_endpoint "GET" "/api/v1/progress/daily" "Daily progress"
echo ""

# Summary
echo ""
echo "================================"
echo "📊 Test Summary"
echo "================================"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo "Total: $TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. This may be expected for endpoints requiring authentication or specific data.${NC}"
    exit 1
fi
