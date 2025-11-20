#!/bin/bash
# Stop all running microservices

echo "Stopping microservices..."

# Find and kill all uvicorn processes
PIDS=$(ps aux | grep -E "uvicorn main:app" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No services running."
else
    echo "Found running services with PIDs: $PIDS"
    for PID in $PIDS; do
        echo "Stopping service (PID: $PID)..."
        kill -9 $PID
    done
    echo "All services stopped."
fi

# Clean up log files
echo "Cleaning up logs..."
rm -f /tmp/edc-service.log
rm -f /tmp/analytics-service.log
rm -f /tmp/data-generation-service.log

echo "Done!"
