#!/bin/bash

# Gremlin ShadTail Trader Launcher with Enhanced System Orchestration
# This script starts all services and opens the Electron app

echo "🚀 Starting Gremlin ShadTail Trader..."
echo "📊 AI-Powered Trading Platform with Grok Integration"

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
        print_error "Node.js not found. Please install Node.js."
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3."
        exit 1
    fi
    
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry not found. Please install Poetry."
        exit 1
    fi
    
    print_success "All dependencies available"
}

# Start Tailscale if available and configuration enables it
start_tailscale() {
    if command -v tailscale &> /dev/null; then
        print_status "Checking Tailscale configuration..."
        
        # Check if auto-start is enabled in config
        if [ -f "backend/Gremlin_Trade_Core/config/FullSpec.config" ]; then
            ENABLE_TAILSCALE=$(python3 -c "
import json
try:
    with open('backend/Gremlin_Trade_Core/config/FullSpec.config', 'r') as f:
        config = json.load(f)
    print(config.get('system_config', {}).get('enable_tailscale_tunnel', False))
except:
    print(False)
" 2>/dev/null)
            
            if [ "$ENABLE_TAILSCALE" = "True" ]; then
                print_status "Auto-starting Tailscale..."
                if ! tailscale status &> /dev/null; then
                    sudo tailscale up
                    if [ $? -eq 0 ]; then
                        print_success "Tailscale started successfully"
                    else
                        print_warning "Failed to start Tailscale"
                    fi
                else
                    print_success "Tailscale already running"
                fi
            else
                print_status "Tailscale auto-start disabled in config"
            fi
        fi
    else
        print_warning "Tailscale not installed"
    fi
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

# Start Electron app
start_electron() {
    print_status "Starting Electron desktop application..."
    
    # Check if frontend is built
    if [ ! -d "frontend/dist" ]; then
        print_status "Building frontend..."
        cd frontend
        npm run build
        cd ..
    fi
    
    # Start Electron app
    cross-env NODE_ENV=production electron . &
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
    echo "   • Grok AI Chat Assistant"
    echo "   • Live Source Code Editor"
    echo "   • Real-time Trading Feed"
    echo "   • System Monitoring & Agent Control"
    echo "   • Tailscale Network Integration"
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
    start_tailscale
    
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
