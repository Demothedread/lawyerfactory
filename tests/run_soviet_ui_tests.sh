#!/bin/bash
# Test runner script for Soviet Control Panel UI
# Executes Puppeteer tests with proper configuration

echo "🚀 Soviet Control Panel UI Test Suite"
echo "====================================="
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install puppeteer jest --save-dev
fi

# Check if the HTML file exists (from project root)
if [ ! -f "../apps/ui/templates/consolidated_factory.html" ]; then
    echo "❌ Error: consolidated_factory.html not found!"
    echo "Please ensure the file exists at: ../apps/ui/templates/consolidated_factory.html"
    exit 1
fi

# Check if the server is running
echo "🔍 Checking if server is running..."
if ! curl -s http://127.0.0.1:8000/apps/ui/templates/consolidated_factory.html > /dev/null; then
    echo "❌ Error: Server not running on port 8000!"
    echo "Please start the server with: ./launch-system.sh --frontend-port 8000 --backend-port 5000"
    exit 1
fi
echo "✅ Server is running"

# Run the tests
echo "🧪 Running Puppeteer tests..."
echo ""

# Run with Jest for full test suite
npx jest tests/test_soviet_control_panel.js --verbose

# Alternative: Direct execution (shows interactive browser)
# node tests/test_soviet_control_panel.js

echo ""
echo "✅ Test execution complete!"