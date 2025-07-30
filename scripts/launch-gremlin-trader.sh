#!/bin/bash

# Gremlin ShadTail Trader Launcher - NO CONSTRAINTS MODE
cd "$(dirname "$0")/.."  # Go to project root directory

echo "🚀 Starting Gremlin ShadTail Trader..."

# Kill any existing processes first
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "python.*server" 2>/dev/null || true

# Export environment variables for no sandbox mode
export ELECTRON_DISABLE_SANDBOX=1
export DISPLAY=${DISPLAY:-:0}

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
        --disable-gpu \
        --disable-web-security \
        --allow-running-insecure-content \
        --disable-features=VizDisplayCompositor &
elif [ -f "dist-electron/Gremlin ShadTail Trader-1.0.0.AppImage" ]; then
    echo "📱 Launching AppImage..."
    chmod +x "dist-electron/Gremlin ShadTail Trader-1.0.0.AppImage"
    "dist-electron/Gremlin ShadTail Trader-1.0.0.AppImage" \
        --no-sandbox \
        --disable-dev-shm-usage \
        --disable-gpu \
        --disable-web-security \
        --allow-running-insecure-content \
        --disable-features=VizDisplayCompositor & \
        --disable-gpu \
        --disable-web-security \
        --allow-running-insecure-content \
        --disable-features=VizDisplayCompositor &
else
    echo "🔧 No packaged version found, launching development version..."
    launch_dev
fi

# Wait a moment for the application to start
sleep 3
echo "✅ Gremlin ShadTail Trader launched successfully!"
echo "💡 If desktop app doesn't appear, check: http://localhost:4321"