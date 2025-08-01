#!/bin/bash

# For Linux users: Launch Gremlin ShadTail Trader with proper backend setup

# Gremlin ShadTail Trader Launcher with Poetry Backend Support
cd "$(dirname "$0")/.."  # Go to project root directory

echo "🚀 Starting Gremlin ShadTail Trader..."

# Kill any existing processes first
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "python.*server" 2>/dev/null || true

# Export environment variables for no sandbox mode
export ELECTRON_DISABLE_SANDBOX=1
export DISPLAY=${DISPLAY:-:0}
export PATH="$HOME/.local/bin:$PATH"

# Ensure backend dependencies are ready
echo "🔧 Preparing backend environment..."
cd backend
if [ -f "pyproject.toml" ]; then
    if ! command -v poetry &> /dev/null; then
        echo "⚠️ Poetry not found, please install it first"
        echo "💡 Run: curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
    
    # Configure and install dependencies if needed
    poetry config virtualenvs.in-project true
    if [ ! -d ".venv" ]; then
        echo "📦 Installing backend dependencies..."
        poetry install
    fi
fi
cd ..

# Function to launch development mode
launch_dev() {
    echo "🛠️ Starting in development mode..."
    npm run start &
    sleep 2
    echo "✅ Gremlin ShadTail Trader started on http://localhost:4321"
    echo "📊 Dashboard will open in your browser automatically"
}

# Check if we have a packaged app and launch with NO CONSTRAINTS
if [ -f "dist-electron/linux-unpacked/gremlin-shadtail-trader" ]; then
    echo "📱 Launching packaged application..."
    "./dist-electron/linux-unpacked/gremlin-shadtail-trader" \
        --no-sandbox \
        --disable-dev-shm-usage \
        --disable-web-security \
        --allow-running-insecure-content &
elif [ -f "dist-electron/Gremlin ShadTail Trader-1.0.0.AppImage" ]; then
    echo "📱 Launching AppImage..."
    chmod +x "dist-electron/Gremlin ShadTail Trader-1.0.0.AppImage"
    "dist-electron/Gremlin ShadTail Trader-1.0.0.AppImage" \
        --no-sandbox \
        --disable-dev-shm-usage \
        --disable-web-security \
        --allow-running-insecure-content &
else
    echo "🔧 No packaged version found, launching development version..."
    launch_dev
fi

# Wait a moment for the application to start
sleep 3
echo "✅ Gremlin ShadTail Trader launched successfully!"
echo "💡 If desktop app doesn't appear, check: http://localhost:4321"