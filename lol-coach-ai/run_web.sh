#!/bin/bash

# LoL Coach AI - Web Server Launcher

echo ""
echo "========================================"
echo "   LOL COACH AI - WEB SERVER"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8+ first."
    echo "Download: https://www.python.org/downloads/"
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing required packages..."
    pip3 install -r requirements.txt
fi

echo ""
echo "🚀 Starting LoL Coach AI Web Server..."
echo ""
echo "   Web UI:     http://localhost:5000"
echo "   Mobile UI:  http://<your-computer-ip>:5000"
echo ""
echo "   To find your IP: Type 'ifconfig' in terminal"
echo "   Look for 'inet' address (usually 192.168.x.x or 10.x.x.x)"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

python3 app.py
