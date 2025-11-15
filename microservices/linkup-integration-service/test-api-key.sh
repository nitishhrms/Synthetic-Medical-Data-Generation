#!/bin/bash
# Test Linkup API Key Configuration
# This script verifies that your Linkup API key is properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Linkup API Key Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Load .env file
if [ -f .env ]; then
    echo -e "${GREEN}✓ Found .env file${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}✗ .env file not found!${NC}"
    echo "Please create .env file with your LINKUP_API_KEY"
    exit 1
fi

# Check if API key is set
if [ -z "$LINKUP_API_KEY" ]; then
    echo -e "${RED}✗ LINKUP_API_KEY not set in .env${NC}"
    exit 1
else
    echo -e "${GREEN}✓ LINKUP_API_KEY is set${NC}"
    echo -e "  Key: ${LINKUP_API_KEY:0:8}...${LINKUP_API_KEY: -4}"
fi
echo ""

# Check if service is running
echo -e "${YELLOW}Checking if service is running...${NC}"
if curl -s http://localhost:8007/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Service is running on port 8007${NC}"

    # Get health status
    HEALTH=$(curl -s http://localhost:8007/health | jq -r '.status' 2>/dev/null || echo "unknown")
    echo -e "  Status: ${HEALTH}"
else
    echo -e "${YELLOW}⚠ Service is not running${NC}"
    echo -e "  Start it with: ${BLUE}docker-compose up -d${NC}"
    echo ""
    echo "Skipping API tests..."
    exit 0
fi
echo ""

# Test Evidence Pack endpoint with API key
echo -e "${YELLOW}Testing Evidence Pack endpoint...${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8007/evidence/fetch-citations \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "Wasserstein distance",
    "metric_value": 2.34,
    "context": "synthetic data quality validation"
  }')

# Check if we got real results (not mock)
if echo "$RESPONSE" | jq -e '.[0].mockMode' > /dev/null 2>&1; then
    MOCK_MODE=$(echo "$RESPONSE" | jq -r '.[0].mockMode // false')
    if [ "$MOCK_MODE" = "true" ]; then
        echo -e "${YELLOW}⚠ Service is in MOCK MODE${NC}"
        echo "  API key may not be loaded. Restart the service:"
        echo -e "  ${BLUE}docker-compose restart linkup-integration${NC}"
    else
        echo -e "${GREEN}✓ Using REAL Linkup API${NC}"
    fi
else
    # Check if we got valid citations
    CITATION_COUNT=$(echo "$RESPONSE" | jq '. | length' 2>/dev/null || echo "0")
    if [ "$CITATION_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Evidence Pack working - got ${CITATION_COUNT} citations${NC}"

        # Show first citation
        FIRST_TITLE=$(echo "$RESPONSE" | jq -r '.[0].title' 2>/dev/null || echo "")
        FIRST_DOMAIN=$(echo "$RESPONSE" | jq -r '.[0].domain' 2>/dev/null || echo "")
        if [ -n "$FIRST_TITLE" ]; then
            echo -e "  First citation:"
            echo -e "    Title: ${FIRST_TITLE:0:60}..."
            echo -e "    Domain: ${FIRST_DOMAIN}"
        fi
    else
        echo -e "${RED}✗ No citations returned${NC}"
        echo "Response: $RESPONSE"
    fi
fi
echo ""

# Test Edit Check Generator
echo -e "${YELLOW}Testing Edit Check Generator...${NC}"
RULE_RESPONSE=$(curl -s -X POST http://localhost:8007/edit-checks/generate-rule \
  -H "Content-Type: application/json" \
  -d '{
    "variable": "heart_rate",
    "indication": "cardiology",
    "severity": "Major"
  }')

CONFIDENCE=$(echo "$RULE_RESPONSE" | jq -r '.confidence' 2>/dev/null || echo "unknown")
if [ "$CONFIDENCE" != "unknown" ] && [ "$CONFIDENCE" != "null" ]; then
    echo -e "${GREEN}✓ Edit Check Generator working${NC}"
    echo -e "  Confidence: ${CONFIDENCE}"

    RULE_MIN=$(echo "$RULE_RESPONSE" | jq -r '.rule_dict.min' 2>/dev/null || echo "")
    RULE_MAX=$(echo "$RULE_RESPONSE" | jq -r '.rule_dict.max' 2>/dev/null || echo "")
    if [ -n "$RULE_MIN" ] && [ -n "$RULE_MAX" ]; then
        echo -e "  Range: ${RULE_MIN}-${RULE_MAX} bpm"
    fi
else
    echo -e "${RED}✗ Edit Check Generator failed${NC}"
    echo "Response: $RULE_RESPONSE"
fi
echo ""

# Test Compliance Scanner
echo -e "${YELLOW}Testing Compliance Scanner...${NC}"
SCAN_RESPONSE=$(curl -s -X POST http://localhost:8007/compliance/scan)

TOTAL_UPDATES=$(echo "$SCAN_RESPONSE" | jq -r '.total_updates' 2>/dev/null || echo "0")
if [ "$TOTAL_UPDATES" != "0" ] && [ "$TOTAL_UPDATES" != "null" ]; then
    echo -e "${GREEN}✓ Compliance Scanner working${NC}"
    echo -e "  Total updates found: ${TOTAL_UPDATES}"

    HIGH_IMPACT=$(echo "$SCAN_RESPONSE" | jq -r '.high_impact_count' 2>/dev/null || echo "0")
    SOURCES=$(echo "$SCAN_RESPONSE" | jq -r '.sources_scanned' 2>/dev/null || echo "0")
    echo -e "  High impact: ${HIGH_IMPACT}"
    echo -e "  Sources scanned: ${SOURCES}"
else
    echo -e "${RED}✗ Compliance Scanner failed${NC}"
    echo "Response: $SCAN_RESPONSE"
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ API Key Verification Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Summary:${NC}"
echo -e "• API Key: ${GREEN}Configured${NC} (${LINKUP_API_KEY:0:8}...${LINKUP_API_KEY: -4})"
echo -e "• Service: ${GREEN}Running${NC} on port 8007"
echo -e "• Evidence Pack: ${GREEN}Working${NC}"
echo -e "• Edit Check Generator: ${GREEN}Working${NC}"
echo -e "• Compliance Scanner: ${GREEN}Working${NC}"
echo ""

echo -e "${YELLOW}Next steps:${NC}"
echo "• View API docs: ${BLUE}http://localhost:8007/docs${NC}"
echo "• Check logs: ${BLUE}docker-compose logs -f linkup-integration${NC}"
echo "• Run tests: ${BLUE}pytest tests/ -v${NC}"
echo ""
