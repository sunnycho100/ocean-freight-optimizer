@echo off
REM Ocean Freight Optimizer - Desktop (Electron) Launcher for Windows

echo ==========================================
echo  Ocean Freight Optimizer Desktop - Start
echo ==========================================
echo.

cd /d "%~dp0"
cd freight-ui

if not exist node_modules (
  echo Installing frontend dependencies...
  npm install
)

echo Starting Electron desktop app in development mode...
npm run desktop:dev
