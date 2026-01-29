#!/bin/bash

# macOS Cleaner Launcher
# This script provides easy access to both GUI and CLI versions

echo "🍎 macOS Cleaner Launcher"
echo "========================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the mac-cleaner directory."
    exit 1
fi

# Check if we are running from the venv
if [[ "$VIRTUAL_ENV" != "" ]] || [ -f "venv/bin/activate" ]; then
    CLEANER_CMD="python3 -m mac_cleaner.cli"
else
    if command -v mac-cleaner >/dev/null 2>&1; then
        CLEANER_CMD="mac-cleaner"
    else
        CLEANER_CMD="python3 -m mac_cleaner.cli"
    fi
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies and package..."
pip install -e . > /dev/null 2>&1

# Menu
echo ""
echo "Choose your option:"
echo "1) Launch Web GUI (Analysis)"
echo "2) Run Command Line Analysis"
echo "3) Dry Run Analysis (CLI)"
echo "4) Exit"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🌐 Launching Web GUI..."
        if [ "$CLEANER_CMD" = "mac-cleaner" ]; then
            mac-cleaner web
        else
            python -m mac_cleaner.web.web_gui
        fi
        ;;
    2)
        echo "🔍 Running Command Line Analysis..."
        if [ "$CLEANER_CMD" = "mac-cleaner" ]; then
            mac-cleaner analyze
        else
            python -m mac_cleaner.cli analyze
        fi
        ;;
    3)
        echo "🔍 Running Dry Run Analysis..."
        python3 -m mac_cleaner.cli analyze --dry-run
        ;;
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please try again."
        exit 1
        ;;
esac

echo ""
echo "✅ Cleaning complete!"
