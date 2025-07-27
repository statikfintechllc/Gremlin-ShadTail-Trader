#!/bin/bash

# Gremlin ShadTail Trader Launcher with Enhanced System Orchestration
# This script starts all services and opens the Electron app

echo "🚀 Starting Gremlin ShadTail Trader..."
echo "📊 AI-Powered Trading Platform with Autonomous Features"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required dependencies are available
check_dependencies() {
    print_status "Checking system dependencies..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found. Please run ./install.sh first."
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please run ./install.sh first."
        exit 1
    fi
    
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry not found. Please run ./install.sh first."
        exit 1
    fi
    
    print_success "All dependencies available"
}

# Start backend with proper error handling
start_backend() {
    print_status "Starting backend services..."
    cd backend
    
    # Check if virtual environment exists
    if ! poetry env list | grep -q "Activated"; then
        print_status "Installing backend dependencies..."
        poetry install --no-root
    fi
    
    # Start backend in background
    poetry run uvicorn dashboard_backend.server:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to start
    print_status "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            print_success "Backend started successfully (PID: $BACKEND_PID)"
            return 0
        fi
        sleep 1
    done
    
    print_error "Backend failed to start within 30 seconds"
    return 1
}

# Start Electron app with cross-platform compatibility
start_electron() {
    print_status "Starting Electron desktop application..."
    
    # Check if frontend is built
    if [ ! -d "frontend/dist" ]; then
        print_status "Building frontend..."
        cd frontend
        npm run build
        cd ..
    fi
    
    # Detect environment and set appropriate flags
    ELECTRON_FLAGS=""
    
    # Check if running in headless environment
    if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
        print_warning "No display detected. Running in headless mode."
        ELECTRON_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --headless"
    else
        # Check if running in container or CI
        if [ -n "$CI" ] || [ -f "/.dockerenv" ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
            ELECTRON_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu"
        fi
    fi
    
    # Start Electron app
    print_status "Starting with flags: $ELECTRON_FLAGS"
    cross-env NODE_ENV=production electron . $ELECTRON_FLAGS &
    ELECTRON_PID=$!
    
    print_success "Electron app started (PID: $ELECTRON_PID)"
    print_success "✅ Gremlin ShadTail Trader is now running!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Web Interface: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Desktop App: Running in Electron"
    echo ""
    echo "📱 Features Available:"
    echo "   • Autonomous Trading System"
    echo "   • Live Market Data Scraping"
    echo "   • AI-Powered Decision Making"
    echo "   • Real-time Vector Embeddings"
    echo "   • Cross-platform Desktop Interface"
    echo ""
    echo "Press Ctrl+C to stop all services"
}

# Cleanup function
cleanup() {
    print_status "Shutting down services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        print_status "Backend stopped"
    fi
    
    if [ ! -z "$ELECTRON_PID" ]; then
        kill $ELECTRON_PID 2>/dev/null
        print_status "Electron app stopped"
    fi
    
    print_success "All services stopped. Goodbye! 👋"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_dependencies
    
    if start_backend; then
        start_electron
        
        # Wait for processes
        wait $BACKEND_PID $ELECTRON_PID
    else
        print_error "Failed to start backend. Exiting."
        exit 1
    fi
}

# Run main function
main
