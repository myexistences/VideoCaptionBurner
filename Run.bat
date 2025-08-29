@echo off
title Application Runner
color 0A
setlocal enabledelayedexpansion

echo =======================================
echo   Checking Python installation...
echo =======================================
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

echo =======================================
echo   Checking required packages...
echo =======================================
set "missing="

for /f "usebackq delims=" %%p in ("requirements.txt") do (
    set "line=%%p"
    rem Trim spaces
    for /f "tokens=* delims= " %%x in ("!line!") do set "line=%%x"

    rem Skip blank lines
    if not "!line!"=="" (
        rem Skip comments
        if not "!line:~0,1!"=="#" (
            for /f "tokens=1 delims==" %%a in ("!line!") do (
                pip show %%a >nul 2>nul
                if errorlevel 1 (
                    set missing=1
                    echo Missing: !line!
                    pip install !line!
                    if errorlevel 1 (
                        echo [ERROR] Failed to install !line!
                        pause
                        exit /b
                    )
                )
            )
        )
    )
)

if not defined missing (
    echo All packages already installed. Skipping installation.
)

cls
echo =======================================
echo        Starting Application...
echo =======================================
python main.py

echo.
echo Press any key to exit...
pause >nul
