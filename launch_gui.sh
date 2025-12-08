#!/bin/bash
# LLM Council - GUI Launcher for Mac/Linux
# Just run: bash launch_gui.sh

echo "Starting LLM Council GUI..."
python3 gui_setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Python 3 is not installed"
    echo ""
    echo "Install Python from: https://www.python.org/"
    echo ""
fi
