#!/bin/bash
# Start microservices for development (without Docker)

echo "Starting microservices..."

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "Installing uvicorn..."
    pip3 install uvicorn fastapi pandas
fi

# Install EDC service dependencies
echo "Installing EDC service dependencies..."
cd /home/user/Synthetic-Medical-Data-Generation/microservices/edc-service
pip3 install -r requirements.txt

# Install Analytics service dependencies
echo "Installing Analytics service dependencies..."
cd /home/user/Synthetic-Medical-Data-Generation/microservices/analytics-service
pip3 install -r requirements.txt

# Install Data Generation service dependencies
echo "Installing Data Generation service dependencies..."
cd /home/user/Synthetic-Medical-Data-Generation/microservices/data-generation-service
pip3 install -r requirements.txt

# Start EDC Service (port 8001)
echo "Starting EDC Service on port 8001..."
cd /home/user/Synthetic-Medical-Data-Generation/microservices/edc-service/src
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/edc-service.log 2>&1 &
EDC_PID=$!
echo "EDC Service started (PID: $EDC_PID)"

# Start Analytics Service (port 8003)
echo "Starting Analytics Service on port 8003..."
cd /home/user/Synthetic-Medical-Data-Generation/microservices/analytics-service/src
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8003 > /tmp/analytics-service.log 2>&1 &
ANALYTICS_PID=$!
echo "Analytics Service started (PID: $ANALYTICS_PID)"

# Start Data Generation Service (port 8002)
echo "Starting Data Generation Service on port 8002..."
cd /home/user/Synthetic-Medical-Data-Generation/microservices/data-generation-service/src
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8002 > /tmp/data-generation-service.log 2>&1 &
DATAGEN_PID=$!
echo "Data Generation Service started (PID: $DATAGEN_PID)"

echo ""
echo "Waiting for services to start..."
sleep 5

echo ""
echo "Testing service health..."
echo "EDC Service (8001): $(curl -s http://localhost:8001/health | grep -o 'healthy' || echo 'NOT RUNNING')"
echo "Analytics Service (8003): $(curl -s http://localhost:8003/health | grep -o 'healthy' || echo 'NOT RUNNING')"
echo "Data Generation Service (8002): $(curl -s http://localhost:8002/health | grep -o 'healthy' || echo 'NOT RUNNING')"

echo ""
echo "Service logs:"
echo "  EDC: tail -f /tmp/edc-service.log"
echo "  Analytics: tail -f /tmp/analytics-service.log"
echo "  Data Generation: tail -f /tmp/data-generation-service.log"

echo ""
echo "To stop services:"
echo "  kill $EDC_PID $ANALYTICS_PID $DATAGEN_PID"

echo ""
echo "All services started!"
