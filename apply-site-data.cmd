@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply-site-data.ps1" %*
set EXIT_CODE=%ERRORLEVEL%

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Generation failed.
    pause
    exit /b %EXIT_CODE%
)

echo.
echo Done.
pause
