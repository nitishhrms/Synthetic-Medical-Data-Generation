@echo off
echo ========================================
echo Starting Data Generation Service
echo Port: 8001
echo ========================================
echo.

cd /d "%~dp0microservices\data-generation-service"

echo Current directory: %CD%
echo.
echo Starting service...
echo Press Ctrl+C to stop the service
echo.

python src\main.py

pause
