@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo         JARVIS Desktop Assistant Launcher         
echo ==================================================

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ and add it to your PATH.
    exit /b 1
)

:: 2. Locate project root (directory containing this script's parent)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

:: 3. Check virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating .venv virtual environment...
    call ".venv\Scripts\activate.bat"
)

:: 4. Run Doctor Check optional argument
if "%1"=="--doctor" (
    echo [INFO] Running JARVIS Subsystem Doctor...
    python -m jarvis --doctor
    exit /b %errorlevel%
)

if "%1"=="--self-test" (
    echo [INFO] Running JARVIS End-to-End Self-Test...
    python -m jarvis --self-test
    exit /b %errorlevel%
)

:: 5. Launch JARVIS Application
echo [INFO] Launching JARVIS...
python -m jarvis %*

endlocal
