@echo off
echo ==========================================
echo Starting All Services
echo ==========================================
echo.

echo Starting Data Generation Service (Port 8001)...
start "Data Generation Service - Port 8001" cmd /k "cd /d %~dp0microservices\data-generation-service && python src\main.py"

echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo Starting Analytics Service (Port 8003)...
start "Analytics Service - Port 8003" cmd /k "cd /d %~dp0microservices\analytics-service && python src\main.py"

echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo Starting Frontend...
start "Frontend - Port 5173" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ==========================================
echo All services are starting!
echo ==========================================
echo.
echo Three terminal windows should have opened:
echo   1. Data Generation Service (Port 8001)
echo   2. Analytics Service (Port 8003)
echo   3. Frontend (Port 5173 or 3000)
echo.
echo Wait for each to finish starting, then open:
echo   http://localhost:5173
echo.
echo Press any key to close this window...
pause >nul
