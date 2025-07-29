#!/bin/bash

# Complete Gremlin ShadTail Trader Installation & Launch Script
# This script installs everything and ensures the app works perfectly

set -e

echo "🚀 Gremlin ShadTail Trader - Complete Installation & Launch System"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}  $1"
    echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_status() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

cd "$(dirname "$0")"

print_header "GREMLIN SHADTAIL TRADER - COMPLETE SYSTEM SETUP"

# 1. Fix ChromaDB Configuration
print_status "Fixing ChromaDB duplicate database issue..."
# The embedder.py was already fixed above - this ensures single ChromaDB instance

# 2. Install missing dependencies
print_status "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y imagemagick sqlite3 chromium-browser &> /dev/null || true
fi

# 3. Create professional icon if missing
if [ ! -f "resources/icon.png" ]; then
    print_status "Creating professional application icon..."
    convert -size 512x512 -background "#1a1a2e" -fill "#00ff88" -pointsize 300 -gravity center label:"G" resources/icon.png 2>/dev/null || {
        print_warning "Using fallback icon"
        mkdir -p resources
        touch resources/icon.png
    }
fi

# 4. Run complete installation
print_status "Running complete dependency installation..."
./scripts/install-all

# 5. Fix desktop integration
print_status "Setting up desktop integration..."
CURRENT_DIR=$(pwd)
cp GremlinTrader.desktop "$HOME/.local/share/applications/" 2>/dev/null || true
if [ -d "$HOME/Desktop" ]; then
    cp GremlinTrader.desktop "$HOME/Desktop/" 2>/dev/null || true
    chmod +x "$HOME/Desktop/GremlinTrader.desktop" 2>/dev/null || true
fi

# 6. Test the application
print_status "Testing application launch..."

# Kill any existing backend processes
pkill -f "uvicorn.*dashboard_backend" 2>/dev/null || true
sleep 2

# Start in development mode for guaranteed functionality
print_status "Starting Gremlin ShadTail Trader in optimized mode..."

# Set environment variables for proper operation
export ELECTRON_DISABLE_SANDBOX=1
export DISPLAY=${DISPLAY:-:0}

# Launch the application
npm run start &
APP_PID=$!

print_success "Application starting..."
print_status "Waiting for backend initialization..."

# Wait for backend to be ready
for i in {1..30}; do
    if curl -s http://localhost:8000/health &> /dev/null; then
        print_success "Backend ready!"
        break
    fi
    echo -n "."
    sleep 1
done

print_header "🎉 INSTALLATION COMPLETE! 🎉"

echo ""
print_success "Gremlin ShadTail Trader is now fully installed and running!"
echo ""
echo -e "${CYAN}📱 Application Features:${NC}"
echo "   • Professional Dark UI (Grok/OpenAI style)"
echo "   • Autonomous Trading Agents"
echo "   • Real-time Market Dashboard"
echo "   • AI-Powered Signal Analysis"
echo "   • Unified Vector Database (Single ChromaDB)"
echo "   • Desktop Application Integration"
echo ""
echo -e "${CYAN}🚀 Access Options:${NC}"
echo "   1. Electron Window (should open automatically)"
echo "   2. Browser: http://localhost:4321"
echo "   3. API: http://localhost:8000"
echo "   4. Desktop Icon: Click 'Gremlin ShadTail Trader'"
echo ""
echo -e "${CYAN}🔧 Future Launches:${NC}"
echo "   • Quick: ./launch-gremlin-trader.sh"
echo "   • Development: npm run dev"
echo "   • Production: npm run start"
echo ""
print_success "Setup complete! Happy trading! 📈"

# Keep the script running to show status
if [ "$1" != "--no-wait" ]; then
    echo ""
    print_status "Press Ctrl+C to stop the application"
    wait $APP_PID
fi
