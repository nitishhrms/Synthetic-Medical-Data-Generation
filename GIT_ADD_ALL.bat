@echo off
echo ============================================
echo Fixing Git Index Issues
echo ============================================
echo.

cd /d "%~dp0"

echo Step 1: Removing nul from git index...
git rm -f --cached "microservices/data-generation-service/src/nul" 2>nul
git rm -f --cached "microservices\data-generation-service\src\nul" 2>nul

echo Step 2: Adding .gitignore rule to prevent this...
echo nul >> .gitignore

echo Step 3: Adding all your files...
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
echo Files staged! Now you can commit:
echo   git commit -m "Add AWS guide, AACT fixes, and service improvements"
echo   git push
echo ============================================
pause
