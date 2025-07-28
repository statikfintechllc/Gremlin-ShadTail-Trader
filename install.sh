#!/bin/bash

# Enhanced install.sh script for Gremlin ShadTail Trader with Universal OS Detection
# This script auto-detects OS and builds the complete system for one-click operation

set -e  # Exit on any error

echo "🚀 Installing Gremlin ShadTail Trader with Enhanced Features..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

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

print_header() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_system() {
    echo -e "${PURPLE}[SYSTEM]${NC} $1"
}

# Comprehensive OS Detection
detect_os() {
    print_header "Detecting Operating System"
    
    OS="unknown"
    ARCH="unknown"
    DISTRO="unknown"
    PACKAGE_MANAGER="unknown"
    
    # Detect architecture
    case $(uname -m) in
        x86_64) ARCH="x64" ;;
        arm64|aarch64) ARCH="arm64" ;;
        armv7l) ARCH="armv7l" ;;
        i386|i686) ARCH="x32" ;;
        *) ARCH="unknown" ;;
    esac
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        
        # Detect Linux distribution
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
            case $DISTRO in
                ubuntu|debian) PACKAGE_MANAGER="apt" ;;
                fedora|rhel|centos) PACKAGE_MANAGER="dnf" ;;
                arch|manjaro) PACKAGE_MANAGER="pacman" ;;
                opensuse*) PACKAGE_MANAGER="zypper" ;;
                alpine) PACKAGE_MANAGER="apk" ;;
                *) PACKAGE_MANAGER="unknown" ;;
            esac
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
        PACKAGE_MANAGER="brew"
        
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        DISTRO="windows"
        PACKAGE_MANAGER="winget"
        
    elif [[ "$OSTYPE" == "freebsd"* ]]; then
        OS="freebsd"
        DISTRO="freebsd"
        PACKAGE_MANAGER="pkg"
    fi
    
    print_system "Operating System: $OS"
    print_system "Architecture: $ARCH"
    print_system "Distribution: $DISTRO"
    print_system "Package Manager: $PACKAGE_MANAGER"
    
    # Set global variables
    export DETECTED_OS="$OS"
    export DETECTED_ARCH="$ARCH"
    export DETECTED_DISTRO="$DISTRO"
    export DETECTED_PACKAGE_MANAGER="$PACKAGE_MANAGER"
}

# Install system dependencies based on OS
install_system_dependencies() {
    print_header "Installing System Dependencies for $DETECTED_OS"
    
    case $DETECTED_OS in
        linux)
            case $DETECTED_PACKAGE_MANAGER in
                apt)
                    print_status "Installing dependencies via apt..."
                    sudo apt update
                    sudo apt install -y curl wget git build-essential python3 python3-pip python3-venv nodejs npm 
                    ;;
                dnf)
                    print_status "Installing dependencies via dnf..."
                    sudo dnf install -y curl wget git gcc gcc-c++ make python3 python3-pip nodejs npm
                    ;;
                pacman)
                    print_status "Installing dependencies via pacman..."
                    sudo pacman -Sy --noconfirm curl wget git base-devel python python-pip nodejs npm
                    ;;
                zypper)
                    print_status "Installing dependencies via zypper..."
                    sudo zypper install -y curl wget git gcc gcc-c++ make python3 python3-pip nodejs npm
                    ;;
                apk)
                    print_status "Installing dependencies via apk..."
                    sudo apk add curl wget git build-base python3 py3-pip nodejs npm
                    ;;
                *)
                    print_warning "Unknown package manager. Please install manually: curl, wget, git, build tools, python3, nodejs, npm"
                    ;;
            esac
            ;;
        macos)
            print_status "Installing dependencies via Homebrew..."
            if ! command -v brew &> /dev/null; then
                print_status "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install node python@3.11 curl wget git
            ;;
        windows)
            print_status "Installing dependencies for Windows..."
            if command -v winget &> /dev/null; then
                winget install -e --id OpenJS.NodeJS
                winget install -e --id Python.Python.3.11
                winget install -e --id Git.Git
            else
                print_warning "Please install Node.js, Python 3.11+, and Git manually on Windows"
            fi
            ;;
        *)
            print_warning "Unsupported OS. Please install Node.js, Python 3.11+, and Git manually"
            ;;
    esac
}

# Enhanced dependency checks with auto-installation
check_and_install_dependencies() {
    print_header "Checking and Installing Dependencies"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_warning "Node.js not found. Attempting to install..."
        install_system_dependencies
        
        if ! command -v node &> /dev/null; then
            print_error "Node.js installation failed. Please install Node.js (version 18 or higher) manually"
            exit 1
        fi
    fi
    
    # Check Node.js version
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version $NODE_VERSION is too old. Please install Node.js 18 or higher"
        exit 1
    fi
    print_success "Node.js $(node --version) found"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm"
        exit 1
    fi
    print_success "npm $(npm --version) found"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 not found. Attempting to install..."
        install_system_dependencies
        
        if ! command -v python3 &> /dev/null; then
            print_error "Python 3 installation failed. Please install Python 3.11 or higher manually"
            exit 1
        fi
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 9 ]; then
        print_error "Python version $PYTHON_VERSION is too old. Please install Python 3.9 or higher"
        exit 1
    fi
    print_success "Python $(python3 --version) found"
    
    # Check Poetry
    if ! command -v poetry &> /dev/null; then
        print_warning "Poetry is not installed. Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
        
        # Add Poetry to PATH in shell profiles
        for profile in ~/.bashrc ~/.zshrc ~/.profile; do
            if [ -f "$profile" ]; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$profile"
            fi
        done
        
        if ! command -v poetry &> /dev/null; then
            print_error "Poetry installation failed. Please install Poetry manually"
            exit 1
        fi
    fi
    print_success "Poetry $(poetry --version) found"
}

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Main installation process
main() {
    print_header "Gremlin ShadTail Trader Universal Installer"
    echo "🤖 AI-Powered Trading Platform with Autonomous Features"
    echo ""
    
    # Detect OS first
    detect_os
    
    # Check and install dependencies
    check_and_install_dependencies
    
    cd "$PROJECT_ROOT"
    
    print_header "Installing Core Dependencies"
    
    print_status "Installing root dependencies..."
    npm install
    
    print_status "Installing frontend dependencies (Astro/React)..."
    if [ -d "frontend" ]; then
        cd frontend
        npm install
        cd ..
    else
        print_warning "Frontend directory not found, skipping frontend dependencies"
    fi
    
    print_status "Installing backend dependencies (FastAPI/Python)..."
    if [ -d "backend" ]; then
        cd backend
        poetry install --no-root
        poetry add numpy pandas httpx yfinance requests  # Ensure required dependencies are installed
        cd ..
    else
        print_warning "Backend directory not found, skipping backend dependencies"
    fi
    
    print_header "Building Complete Application"
    
    print_status "Building frontend application..."
    if [ -d "frontend" ]; then
        cd frontend
        npm run build
        if [ $? -eq 0 ]; then
            print_success "Frontend built successfully"
        else
            print_error "Frontend build failed"
            exit 1
        fi
        cd ..
    fi
    
    print_status "Building backend application..."
    if [ -d "backend" ]; then
        cd backend
        poetry build
        if [ $? -eq 0 ]; then
            print_success "Backend built successfully"
        else
            print_warning "Backend build completed with warnings"
        fi
        cd ..
    fi
    
    print_status "Building Electron application..."
    npm run build
    if [ $? -eq 0 ]; then
        print_success "Application built successfully"
    else
        print_error "Application build failed"
        exit 1
    fi
    
    create_launch_scripts
    setup_desktop_integration
    install_tailscale_if_needed
    
    print_header "Installation Complete!"
    print_success "🎉 Gremlin ShadTail Trader is ready to use!"
    echo ""
    print_status "To start the application:"
    echo "  • Double-click the desktop icon (if created)"
    echo "  • Run: ./launch-gremlin-trader.sh"
    echo "  • Run: npm start"
    echo ""
    print_status "The application includes:"
    echo "  ✓ Autonomous trading system with live market data"
    echo "  ✓ AI-powered decision making with vector embeddings"
    echo "  ✓ Real-time market scraping and analysis" 
    echo "  ✓ Cross-platform Electron interface"
    echo "  ✓ FastAPI backend with comprehensive APIs"
    echo "  ✓ Grok AI integration for enhanced intelligence"
    echo ""
    print_success "Setup complete! Ready for autonomous trading! 📈🤖"
}

create_launch_scripts() {
    print_header "Creating Launch Scripts"

    # Create enhanced launcher script
    cat > launch-gremlin-trader.sh << 'EOF'
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
EOF
    
    chmod +x launch-gremlin-trader.sh
    print_success "Launch script created: launch-gremlin-trader.sh"
}

setup_desktop_integration() {
    print_header "Setting Up Desktop Integration"
    
    case $DETECTED_OS in
        linux)
            # Create .desktop file for Linux
            cat > GremlinTrader.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Gremlin ShadTail Trader
Comment=AI-Powered Autonomous Trading Platform
Exec=$PROJECT_ROOT/launch-gremlin-trader.sh
Icon=$PROJECT_ROOT/resources/icon.png
Path=$PROJECT_ROOT
Terminal=false
Categories=Office;Finance;
StartupNotify=true
EOF
            
            chmod +x GremlinTrader.desktop
            
            # Copy to desktop and applications
            if [ -d "$HOME/Desktop" ]; then
                cp GremlinTrader.desktop "$HOME/Desktop/"
                print_success "✓ Desktop launcher created"
            fi
            
            if [ -d "$HOME/.local/share/applications" ]; then
                cp GremlinTrader.desktop "$HOME/.local/share/applications/"
                print_success "✓ Application menu entry created"
            fi
            ;;
            
        macos)
            # Create app bundle for macOS
            print_status "Creating macOS app bundle..."
            mkdir -p "Gremlin ShadTail Trader.app/Contents/MacOS"
            mkdir -p "Gremlin ShadTail Trader.app/Contents/Resources"
            
            cat > "Gremlin ShadTail Trader.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch-gremlin-trader</string>
    <key>CFBundleIdentifier</key>
    <string>com.gremlin.shadtail-trader</string>
    <key>CFBundleName</key>
    <string>Gremlin ShadTail Trader</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>
EOF
            
            cp launch-gremlin-trader.sh "Gremlin ShadTail Trader.app/Contents/MacOS/launch-gremlin-trader"
            chmod +x "Gremlin ShadTail Trader.app/Contents/MacOS/launch-gremlin-trader"
            
            if [ -f "resources/icon.icns" ]; then
                cp "resources/icon.icns" "Gremlin ShadTail Trader.app/Contents/Resources/"
            fi
            
            print_success "✓ macOS app bundle created"
            ;;
            
        windows)
            # Create batch file for Windows
            cat > launch-gremlin-trader.bat << 'EOF'
@echo off
echo Starting Gremlin ShadTail Trader...
echo AI-Powered Autonomous Trading Platform

cd /d "%~dp0"

REM Check dependencies
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Node.js not found. Please run install.sh first.
    pause
    exit /b 1
)

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python not found. Please run install.sh first.
    pause
    exit /b 1
)

REM Start backend
echo Starting backend...
cd backend
start /b poetry run uvicorn dashboard_backend.server:app --host 0.0.0.0 --port 8000
cd ..

REM Wait for backend
timeout /t 5 /nobreak >nul

REM Start Electron
echo Starting Electron app...
npm start

pause
EOF
            
            print_success "✓ Windows launcher created: launch-gremlin-trader.bat"
            ;;
    esac
}

install_tailscale_if_needed() {
    print_header "Installing Tailscale (Optional)"
    
    # Check if Tailscale is already installed
    if command -v tailscale &> /dev/null; then
        print_success "Tailscale already installed"
        return
    fi
    
    case $DETECTED_OS in
        linux)
            print_status "Installing Tailscale for Linux..."
            curl -fsSL https://tailscale.com/install.sh | sh
            ;;
        macos)
            if command -v brew &> /dev/null; then
                print_status "Installing Tailscale via Homebrew..."
                brew install tailscale
            else
                print_warning "Please install Tailscale manually from https://tailscale.com/download"
            fi
            ;;
        windows)
            print_warning "Please install Tailscale manually from https://tailscale.com/download"
            ;;
        *)
            print_warning "Please install Tailscale manually from https://tailscale.com/download"
            ;;
    esac
}

# Run main function
main