@echo off
echo ============================================
echo Cleaning up and staging files
echo ============================================
echo.

cd /d "%~dp0"

echo Step 1: Deleting physical nul file...
if exist "microservices\data-generation-service\src\nul" (
    del /f /q "microservices\data-generation-service\src\nul"
    echo   - Deleted nul file
) else (
    echo   - nul file not found (good!)
)

echo.
echo Step 2: Adding nul to .gitignore...
findstr /C:"nul" .gitignore >nul 2>&1
if errorlevel 1 (
    echo nul >> .gitignore
    echo   - Added to .gitignore
) else (
    echo   - Already in .gitignore
)

echo.
echo Step 3: Staging your files...
git add .claude/settings.local.json
git add AWS_guide.md
git add data/aact/scripts/04_patch_aact_cache.py
git add microservices/data-generation-service/src/main.py
git add frontend/src/services/api.ts
git add frontend/src/services/aactApi.ts
git add frontend/src/components/screens/SystemCheck.tsx
git add frontend/src/components/screens/Settings.tsx
git add frontend/src/components/screens/DaftAnalytics.tsx
git add START_ALL.bat
git add FIX_AND_START.bat
git add .gitignore

echo.
echo ============================================
echo Success! Files are staged.
echo.
echo Now run:
echo   git commit -m "Add AWS guide, AACT fixes, and service improvements"
echo   git push
echo ============================================
pause
