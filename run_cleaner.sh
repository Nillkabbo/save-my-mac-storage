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

if command -v mac-cleaner >/dev/null 2>&1; then
    CLEANER_CMD="mac-cleaner"
else
    CLEANER_CMD="python -m mac_cleaner.cli"
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Menu
echo ""
echo "Choose your option:"
echo "1) Launch GUI (Recommended)"
echo "2) Launch Detailed Analysis GUI"
echo "3) Launch Web GUI (Browser-based)"
echo "4) Run Command Line Version"
echo "5) Dry Run Only (CLI)"
echo "6) Exit"
echo ""

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo "🚀 Launching GUI..."
        if [ "$CLEANER_CMD" = "mac-cleaner" ]; then
            mac-cleaner gui
        else
            python -m mac_cleaner.gui
        fi
        ;;
    2)
        echo "🔍 Launching Detailed Analysis GUI..."
        if [ "$CLEANER_CMD" = "mac-cleaner" ]; then
            mac-cleaner detailed-gui
        else
            python -m mac_cleaner.detailed_gui
        fi
        ;;
    3)
        echo "🌐 Launching Web GUI..."
        echo "📋 Opening browser interface..."
        if [ "$CLEANER_CMD" = "mac-cleaner" ]; then
            mac-cleaner web
        else
            python -m mac_cleaner.web_gui
        fi
        ;;
    4)
        echo "🚀 Starting Command Line Cleaner..."
        if [ "$CLEANER_CMD" = "mac-cleaner" ]; then
            mac-cleaner clean --no-dry-run --category all
        else
            python -m mac_cleaner.cli clean --no-dry-run --category all
        fi
        ;;
    5)
        echo "🔍 Running Dry Run Analysis..."
        if [ "$CLEANER_CMD" = "mac-cleaner" ]; then
            mac-cleaner clean --dry-run --category all
        else
            python -m mac_cleaner.cli clean --dry-run --category all
        fi
        ;;
    6)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "✅ Cleaning complete!"
