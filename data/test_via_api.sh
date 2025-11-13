#!/bin/bash
# Test generators via the microservice API

echo "Testing Data Generation Service API..."
echo ""

# Check if service is running
if ! curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "❌ Data Generation Service is not running on port 8002"
    echo "Start it with: docker-compose up data-generation-service"
    exit 1
fi

echo "✅ Service is running"
echo ""

# Test MVN generation
echo "Testing MVN generator..."
curl -s -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 5,
    "target_effect": -5.0,
    "seed": 123
  }' | python3 -m json.tool | head -50

echo ""
echo "Testing Bootstrap generator..."
curl -s -X POST http://localhost:8002/generate/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 5,
    "target_effect": -5.0,
    "seed": 42
  }' | python3 -m json.tool | head -50
