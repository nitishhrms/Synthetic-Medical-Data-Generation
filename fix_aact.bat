@echo off
echo ========================================
echo AACT Cache Fix Script
echo ========================================
echo.

echo Step 1: Restoring AACT cache from git...
git checkout data/aact/processed/aact_statistics_cache.json
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Git restore failed
    pause
    exit /b 1
)
echo ✓ Cache restored
echo.

echo Step 2: Applying demographics patch...
python patch_minimal.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Patch failed
    pause
    exit /b 1
)
echo ✓ Patch applied
echo.

echo Step 3: Testing AACT integration...
python data\aact\scripts\03_test_integration.py
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Integration test had issues
)
echo.

echo ========================================
echo Fix complete! 
echo ========================================
echo.
echo Next steps:
echo 1. Start data-generation-service: cd microservices\data-generation-service ^&^& python src\main.py
echo 2. Test generation endpoint
echo 3. Start analytics-service and test
echo.
pause
