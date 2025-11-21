@echo off
echo ==========================================
echo Fixing Port 8001 Service
echo ==========================================
echo.

echo Step 1: Finding process on port 8001...
netstat -ano | findstr :8001
echo.

echo Step 2: Killing process...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    echo Killing PID: %%a
    taskkill /PID %%a /F
)
echo.

echo Step 3: Waiting 2 seconds...
timeout /t 2 /nobreak >nul
echo.

echo Step 4: Starting Data Generation Service...
cd /d "%~dp0microservices\data-generation-service"
echo Current directory: %CD%
echo.
echo Starting service on port 8001...
echo.
python src\main.py
