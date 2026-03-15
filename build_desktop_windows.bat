@echo off
setlocal

echo ==========================================
echo  Ocean Freight Optimizer - Windows Build
echo ==========================================
echo.

cd /d "%~dp0"
cd freight-ui

if not exist node_modules (
  echo Installing frontend dependencies...
  call npm install
  if errorlevel 1 goto :fail
)

echo Building Windows desktop installer...
call npm run desktop:build
if errorlevel 1 goto :fail

echo.
echo Build complete.
echo Output folder:
echo   %cd%\dist
echo.
echo Installer file:
dir /b "dist\*Setup*.exe" 2>nul
echo.
goto :end

:fail
echo.
echo Build failed.
exit /b 1

:end
endlocal
