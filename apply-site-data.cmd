@echo off
setlocal
set SCRIPT_DIR=%~dp0

if "%~1"=="" (
    echo 未指定 js 文件，自动选择 WebStackPage.github.io-master 目录里最新的 site-data*.js
    python "%SCRIPT_DIR%apply_site_data.py"
) else (
    echo 使用指定文件：%~1
    python "%SCRIPT_DIR%apply_site_data.py" "%~1"
)

if errorlevel 1 (
    echo.
    echo 更新失败。
    pause
    exit /b %errorlevel%
)

echo.
echo 已覆盖当前 site-data.js 和 indexnew2.html
pause
