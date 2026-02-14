#!/bin/bash
# Newsloom API Server 启动脚本

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   🗞️  NEWSLOOM API SERVER LAUNCHER                       ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

echo "✓ Python: $($PYTHON_CMD --version)"

# Check if in correct directory
if [ ! -d "server" ]; then
    echo "❌ Please run this script from the Newsloom project root"
    exit 1
fi

# Check dependencies
echo "🔍 Checking dependencies..."
if ! $PYTHON_CMD -c "import fastapi" 2>/dev/null; then
    echo "⚠️  FastAPI not installed. Installing dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
fi

echo "✓ Dependencies installed"
echo ""

# Create data directory if needed
mkdir -p data

# Start server
echo "🚀 Starting Newsloom API Server..."
echo ""
exec $PYTHON_CMD -m server.main
