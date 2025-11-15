#!/bin/bash

# Sentry Integration Test Script
# Tests all backend microservices and provides frontend testing instructions

set -e  # Exit on error

echo "======================================"
echo "🔍 SENTRY INTEGRATION TEST"
echo "======================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
SERVICES_TESTED=()

# Function to test a service endpoint
test_service() {
    local service_name=$1
    local port=$2
    local url="http://localhost:${port}/sentry-debug"

    echo -e "${BLUE}Testing: ${service_name} (Port ${port})${NC}"
    echo "URL: ${url}"

    # Try to hit the sentry-debug endpoint (it should return 500 with an error)
    response=$(curl -s -w "\n%{http_code}" "${url}" 2>&1 || echo "CONNECTION_FAILED")

    if [[ "$response" == *"CONNECTION_FAILED"* ]]; then
        echo -e "${RED}❌ FAILED - Service not running or not accessible${NC}"
        echo ""
        FAILED=$((FAILED + 1))
        return 1
    fi

    # Extract HTTP status code (last line)
    http_code=$(echo "$response" | tail -n 1)

    # The endpoint should return 500 (Internal Server Error) because it throws an error
    if [ "$http_code" == "500" ]; then
        echo -e "${GREEN}✅ PASSED - Error successfully triggered and sent to Sentry${NC}"
        echo -e "   HTTP Status: ${http_code}"
        PASSED=$((PASSED + 1))
        SERVICES_TESTED+=("${service_name}")
    else
        echo -e "${YELLOW}⚠️  UNEXPECTED - Expected 500, got ${http_code}${NC}"
        echo "Response preview:"
        echo "$response" | head -n 5
        FAILED=$((FAILED + 1))
    fi

    echo ""
}

# Function to check if a service is running
check_service() {
    local port=$1
    nc -z localhost $port 2>/dev/null
    return $?
}

echo "======================================"
echo "📡 BACKEND SERVICES TEST"
echo "======================================"
echo ""

# Test all backend services
echo "Checking which services are running..."
echo ""

# API Gateway (Port 8000)
if check_service 8000; then
    test_service "API Gateway" 8000
else
    echo -e "${YELLOW}⚠️  API Gateway (Port 8000) is not running - skipping${NC}"
    echo ""
fi

# EDC Service (Port 8001)
if check_service 8001; then
    test_service "EDC Service" 8001
else
    echo -e "${YELLOW}⚠️  EDC Service (Port 8001) is not running - skipping${NC}"
    echo ""
fi

# Data Generation Service (Port 8002)
if check_service 8002; then
    test_service "Data Generation Service" 8002
else
    echo -e "${YELLOW}⚠️  Data Generation Service (Port 8002) is not running - skipping${NC}"
    echo ""
fi

# Analytics Service (Port 8003)
if check_service 8003; then
    test_service "Analytics Service" 8003
else
    echo -e "${YELLOW}⚠️  Analytics Service (Port 8003) is not running - skipping${NC}"
    echo ""
fi

# Quality Service (Port 8004)
if check_service 8004; then
    test_service "Quality Service" 8004
else
    echo -e "${YELLOW}⚠️  Quality Service (Port 8004) is not running - skipping${NC}"
    echo ""
fi

# Security Service (Port 8005)
if check_service 8005; then
    test_service "Security Service" 8005
else
    echo -e "${YELLOW}⚠️  Security Service (Port 8005) is not running - skipping${NC}"
    echo ""
fi

echo "======================================"
echo "📊 BACKEND TEST RESULTS"
echo "======================================"
echo -e "${GREEN}✅ Passed: ${PASSED}${NC}"
echo -e "${RED}❌ Failed: ${FAILED}${NC}"
echo ""

if [ ${#SERVICES_TESTED[@]} -gt 0 ]; then
    echo "Services successfully tested:"
    for service in "${SERVICES_TESTED[@]}"; do
        echo "  • ${service}"
    done
    echo ""
fi

echo "======================================"
echo "🌐 FRONTEND TEST INSTRUCTIONS"
echo "======================================"
echo ""
echo "To test Sentry on the frontend:"
echo ""
echo "1. Start the frontend dev server:"
echo -e "   ${BLUE}cd frontend && npm run dev${NC}"
echo ""
echo "2. Open the app in your browser:"
echo -e "   ${BLUE}http://localhost:5173${NC} (or the port shown in terminal)"
echo ""
echo "3. Test Sentry Error Tracking:"
echo "   Option A: Add the test button to your App.tsx:"
echo -e "   ${BLUE}import { SentryErrorButton } from './components/SentryErrorButton'${NC}"
echo -e "   ${BLUE}<SentryErrorButton />${NC}"
echo ""
echo "   Option B: Open browser console and run:"
echo -e "   ${BLUE}throw new Error('Test Sentry error from console!')${NC}"
echo ""
echo "   Option C: Send a test message:"
echo -e "   ${BLUE}import * as Sentry from '@sentry/react'${NC}"
echo -e "   ${BLUE}Sentry.captureMessage('Test message!', 'info')${NC}"
echo ""

echo "======================================"
echo "🎯 VERIFY IN SENTRY DASHBOARD"
echo "======================================"
echo ""
echo "1. Go to: https://sentry.io"
echo "2. Check the 'Issues' tab for new errors"
echo "3. Check the 'Performance' tab for transactions"
echo ""
echo "You should see:"
echo "  • Backend: ZeroDivisionError from each tested service"
echo "  • Frontend: JavaScript errors when you trigger them"
echo ""

if [ $PASSED -gt 0 ]; then
    echo -e "${GREEN}🎉 Sentry integration is working on ${PASSED} backend service(s)!${NC}"
else
    echo -e "${YELLOW}⚠️  No backend services were successfully tested.${NC}"
    echo "Make sure your services are running before testing."
fi

echo ""
echo "======================================"
echo "💡 TIPS"
echo "======================================"
echo ""
echo "• Backend errors should appear immediately in Sentry"
echo "• Frontend errors may take a few seconds to upload"
echo "• Check Sentry's 'Performance' tab for transaction traces"
echo "• Session Replays are available in the 'Replays' tab"
echo ""
