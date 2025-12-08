@echo off
REM LLM Council - GUI Launcher for Windows
REM Just double-click this file to start!

echo Starting LLM Council GUI...
python gui_setup.py

if errorlevel 1 (
    echo.
    echo Error: Python is not installed or not found in PATH
    echo.
    echo Please install Python from: https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
)
