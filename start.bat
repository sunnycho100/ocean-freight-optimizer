@echo off
REM Freight Route Optimizer - Startup Script for Windows
REM This script starts both the API server and React frontend

echo ==========================================
echo  Freight Route Optimizer - Starting...
echo ==========================================
echo.

REM Get the directory where this script is located
cd /d "%~dp0"

REM Start the Flask API server in a new window
echo Starting API server on port 5000...
start "API Server" /min cmd /k ".venv\Scripts\python.exe api_server.py"

REM Wait a moment for API to initialize
timeout /t 3 /nobreak > nul

REM Start the React frontend in a new window
echo Starting React frontend on port 3000...
cd freight-ui
set BROWSER=none
start "React Frontend" /min cmd /k "npm start"

REM Wait for React to compile
echo.
echo Waiting for React to compile (10 seconds)...
timeout /t 10 /nobreak > nul

REM Open browser
echo Opening browser at http://localhost:3000
start http://localhost:3000

echo.
echo ==========================================
echo  Both servers are running!
echo  - API Server:  http://localhost:5000
echo  - Frontend:    http://localhost:3000
echo ==========================================
echo.
echo Press any key to exit this window...
pause > nul
