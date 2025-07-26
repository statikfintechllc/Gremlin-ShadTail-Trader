# Gremlin ShadTail Trader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![Electron](https://img.shields.io/badge/Electron-27+-blueviolet.svg)](https://www.electronjs.org/)

GremlinGPT's standalone trading core designed as a comprehensive, AI-powered trading platform with **Grok AI integration**, **live source editing**, and **Tailscale PWA publishing**. This application serves as both a standalone desktop application and a foundation for VSCode plugin integration.

## 🚀 Overview

Gremlin ShadTail Trader combines modern web technologies with powerful backend processing to deliver a seamless trading experience:

- **🤖 Grok AI Chat Integration** - Direct chat interface with Grok AI for trading insights and code assistance
- **📝 Live Source Code Editor** - Built-in Monaco editor with file tree navigation for real-time code editing
- **📊 Real-time Trading Dashboard** - Monitor market data and trading signals
- **🔌 Modular Plugin Architecture** - Extensible plugin system for adding new functionality
- **🌐 Tailscale PWA Publishing** - Share your trading dashboard securely via Tailscale tunnel
- **🖥️ Cross-Platform Desktop App** - Built with Electron for Windows, macOS, and Linux
- **⚡ Modern Web Interface** - Responsive UI built with Astro, React, and Tailwind CSS
- **🏃 High-Performance Backend** - FastAPI-powered REST API with WebSocket support
- **🧠 Vector Memory System** - Advanced memory management for trading strategies

![Gremlin ShadTail Trader - Source Editor](https://github.com/user-attachments/assets/17561fc2-57d0-49a7-8c59-b1288772e099)

![Gremlin ShadTail Trader - Settings](https://github.com/user-attachments/assets/8f4603e6-fc5d-407e-adec-d1537b124d0c)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   Electron      │◄──►│   Frontend       │◄──►│   Backend       │
│   (Desktop App) │    │   (Astro/React)  │    │   (FastAPI)     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
    │  Main   │              │  Plugin │              │  API    │
    │ Process │              │ System  │              │ Routes  │
    └─────────┘              └─────────┘              └─────────┘
                                  │
                        ┌─────────▼─────────┐
                        │                   │
                   ┌────▼────┐         ┌────▼────┐
                   │  Grok   │         │ Source  │
                   │ Plugin  │         │ Editor  │
                   └─────────┘         └─────────┘
```

### Technology Stack

- **Frontend**: Astro 4.0, React 18, Tailwind CSS 3.4, Monaco Editor
- **Backend**: FastAPI, Python 3.11+, Uvicorn, Plugin Architecture
- **Desktop**: Electron 27, Tailscale Integration
- **AI Integration**: Grok API support with fallback mock responses
- **Build Tools**: Vite, PostCSS, Autoprefixer
- **Package Management**: npm (frontend), Poetry (backend)
- **Development**: Hot reload, TypeScript support

## 📁 Directory Structure

```
gremlin-shadtail-trader/
├── backend/                          # FastAPI backend application
│   ├── Gremlin_Trade_Core/          # Core trading logic
│   │   ├── config/                  # Configuration files
│   │   │   ├── FullSpec.config      # 🆕 Comprehensive config (API keys, logins)
│   │   │   ├── Gremlin_Trade_Config/
│   │   │   │   ├── memory.json      # Memory system config
│   │   │   │   ├── trade_agents.config
│   │   │   │   └── trade_strategy.config
│   │   │   └── Gremlin_Trade_Logs/  # System logs
│   │   ├── plugins/                 # 🆕 Plugin system
│   │   │   ├── __init__.py         # Plugin manager
│   │   │   └── grok/               # 🆕 Grok AI plugin
│   │   │       └── __init__.py     # Grok chat implementation
│   │   ├── Gremlin_Trader_Tools/   # Trading agent tools
│   │   └── globals.py              # Global configuration & utilities
│   ├── Gremlin_Trade_Memory/       # Vector memory system
│   ├── server.py                   # Main FastAPI application
│   └── pyproject.toml              # Python dependencies
├── frontend/                        # Astro frontend application
│   ├── src/
│   │   ├── components/             # React components
│   │   │   ├── Dashboard.tsx       # 🆕 Enhanced tabbed dashboard
│   │   │   ├── GrokChat.tsx        # 🆕 Grok AI chat interface
│   │   │   └── SourceEditor.tsx    # 🆕 Monaco source code editor
│   │   ├── pages/                  # Astro pages
│   │   │   └── index.astro         # Landing page
│   │   └── utils/                  # Utility functions
│   │       └── logger.ts           # Frontend logging system
│   ├── astro.config.mjs           # Astro configuration
│   ├── tailwind.config.cjs        # Tailwind CSS configuration
│   └── package.json               # Frontend dependencies
├── electron/                       # Electron main process
│   ├── main.js                    # Main Electron process
│   └── preload.js                 # Preload script for IPC
├── scripts/                       # Build and utility scripts
│   └── install-all               # Legacy dependency installation script
├── install.sh                    # 🆕 Enhanced installation script
├── launch-gremlin-trader.sh       # 🆕 Application launcher
├── package.json                   # Root package.json (monorepo)
└── README.md                      # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- **Node.js 18+** - [Download here](https://nodejs.org/)
- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Poetry** - [Installation guide](https://python-poetry.org/docs/#installation)
- **Tailscale** (Optional) - [Download here](https://tailscale.com/download)

### Quick Start with Enhanced Installer

1. **Clone the repository**
   ```bash
   git clone https://github.com/statikfintechllc/Gremlin-ShadTail-Trader.git
   cd Gremlin-ShadTail-Trader
   ```

2. **Run the enhanced installation script**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

   This will:
   - Install all dependencies (Node.js, Python, Poetry packages)
   - Set up the Grok plugin system
   - Install Tailscale (if available)
   - Create desktop launcher
   - Build the application

3. **Configure API keys (Optional)**
   ```bash
   # Edit the configuration file to add your API keys
   nano backend/Gremlin_Trade_Core/config/FullSpec.config
   ```

4. **Launch the application**
   ```bash
   ./launch-gremlin-trader.sh
   # or
   npm run dev
   ```

This will start:
- Backend API server on `http://localhost:8000`
- Frontend dev server on `http://localhost:4321`
- Electron desktop application (optional)

### Manual Setup

If you prefer to set up each component manually:

#### Backend Setup
```bash
cd backend
poetry install --no-root
poetry add numpy pandas httpx  # Additional dependencies
poetry run uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm install @monaco-editor/react lucide-react  # Additional UI dependencies
npm run dev
```

#### Electron Setup
```bash
npm install
npm run dev:electron
```

## 🎯 New Features & Usage

### 🤖 Grok AI Chat Integration

The integrated Grok AI assistant provides intelligent trading insights and coding assistance:

**Features:**
- Real-time chat interface with Grok AI
- Trading strategy analysis and recommendations
- Code debugging and generation assistance
- Persistent chat history
- Context-aware responses (trading vs. coding)

**API Endpoints:**
- `POST /api/grok/chat` - Send message to Grok AI
- `GET /api/grok/history` - Retrieve chat history
- `POST /api/grok/clear` - Clear chat history

**Usage:**
1. Click the "Grok Chat" tab in the dashboard
2. Type your question about trading strategies, market analysis, or code
3. Get intelligent responses with trading context

### 📝 Source Code Editor

Built-in Monaco editor for live code editing with full project access:

**Features:**
- File tree navigation of entire project
- Syntax highlighting for Python, JavaScript, TypeScript, JSON, etc.
- Auto-save functionality with backup creation
- Agent start/stop controls
- Real-time file loading and saving

**API Endpoints:**
- `GET /api/source/files` - Get project file tree
- `GET /api/source/file?path=<path>` - Load file content
- `POST /api/source/save` - Save file changes

**Usage:**
1. Click the "Source" tab in the dashboard
2. Navigate the file tree on the left
3. Click any file to open it in the Monaco editor
4. Edit and save files directly from the browser

### 🔌 Plugin Architecture

Extensible plugin system for adding new functionality:

**Features:**
- Base plugin class with standard interface
- Plugin manager for loading/unloading plugins
- Route registration system
- UI component integration

**Adding a New Plugin:**
```python
from backend.Gremlin_Trade_Core.plugins import BasePlugin

class MyPlugin(BasePlugin):
    def initialize(self):
        # Plugin initialization logic
        return True
    
    def get_routes(self):
        # Return FastAPI routes
        return [{"path": "/api/my-plugin", "method": "GET", "handler": self.my_handler}]
```

### 🌐 Tailscale PWA Publishing

Secure remote access to your trading dashboard:

**Features:**
- Tailscale tunnel integration
- PWA publishing via Tailscale's local HTTP server
- QR code generation for mobile access
- Secure remote trading dashboard access

**Setup:**
1. Install Tailscale: `./install.sh` (includes Tailscale)
2. Configure auth key in `FullSpec.config`
3. Enable tunnel publishing in Settings
4. Share dashboard via secure Tailscale network

### 🎛️ Enhanced Dashboard

Multi-tab interface with comprehensive functionality:

**Tabs:**
- **Trading** - Real-time market data and signals
- **Grok Chat** - AI assistant interface
- **Source** - Code editor with file navigation
- **Agents** - Agent control and system monitoring
- **Settings** - System configuration and plugin management

### ⚙️ Configuration System

Comprehensive configuration through `FullSpec.config`:

```json
{
  "api_keys": {
    "grok": {
      "api_key": "your_grok_api_key",
      "base_url": "https://api.x.ai/v1",
      "model": "grok-beta"
    },
    "ibkr": {
      "username": "your_ibkr_username",
      "password": "your_ibkr_password"
    }
  },
  "system_config": {
    "plugins": {
      "grok": {"enabled": true},
      "source_editor": {"enabled": true}
    },
    "pwa_publishing": {
      "enabled": false,
      "tunnel_name": "gremlin-trader"
    }
  }
}
```

## 🎮 Usage

### Development Mode

Start all services in development mode:
```bash
npm run dev
# or
./launch-gremlin-trader.sh
```

Access the application:
- **Web Interface**: http://localhost:4321
- **API Documentation**: http://localhost:8000/docs
- **Desktop App**: Launches automatically

### Production Build

Build the application for production:
```bash
npm run build
npm start
```

### Individual Services

Run services independently:
```bash
# Backend only
npm run dev:backend

# Frontend only
npm run dev:frontend

# Electron only (requires backend/frontend to be running)
npm run dev:electron
```

## 📡 API Endpoints

### Trading & Core Features
- **GET** `/api/feed` - Get current trading data
- **POST** `/api/scan` - Run custom market scan
- **GET** `/api/settings` - Get current settings
- **POST** `/api/settings` - Update settings
- **GET** `/api/memory?q={query}` - Query vector memory store
- **GET** `/api/system/status` - Get comprehensive system status

### Grok AI Integration
- **POST** `/api/grok/chat` - Chat with Grok AI
- **GET** `/api/grok/history` - Get chat history
- **POST** `/api/grok/clear` - Clear chat history

### Source Editor
- **GET** `/api/source/files` - Get project file tree
- **GET** `/api/source/file?path={path}` - Get file content
- **POST** `/api/source/save` - Save file content

### Agent Control
- **GET** `/api/agents/status` - Get agent status
- **POST** `/api/agents/start` - Start agents
- **POST** `/api/agents/stop` - Stop agents

### Plugin System
- **GET** `/api/plugins` - Get loaded plugins status

### Example Usage

```javascript
// Chat with Grok AI
const grokResponse = await fetch('http://localhost:8000/api/grok/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'What trading strategy would you recommend for penny stocks?',
    context: 'trading'
  })
});

// Load file content in source editor
const fileContent = await fetch('http://localhost:8000/api/source/file?path=backend/server.py');

// Get trading feed
const tradingData = await fetch('http://localhost:8000/api/feed');
```

## 🎛️ UI Features

### Enhanced Dashboard Components

- **🤖 Grok AI Chat Interface** - Real-time chat with trading context
- **📝 Source Code Editor** - Monaco editor with project file tree
- **📊 Trading Feed Display** - Real-time market data with color-coded performance
- **👥 Agent Control Panel** - Start/stop agents and view system status
- **⚙️ Settings Panel** - Configure scan intervals, symbols, and plugin settings
- **📱 Responsive Design** - Adapts to different screen sizes
- **🌙 Dark Theme** - Modern dark interface optimized for trading

### Interaction Features

- **💬 Live AI Chat** - Direct communication with Grok AI assistant
- **📂 File Navigation** - Browse and edit any file in the project
- **🔄 Live Data Updates** - Automatic refresh based on scan interval
- **🎯 Symbol Management** - Add/remove symbols from watchlist
- **🛠️ Agent Management** - Start/stop trading agents with visual feedback
- **❌ Error Handling** - Graceful error display and recovery
- **⏳ Loading States** - Visual feedback during data fetching and AI responses

## 🔧 Development

### Project Scripts

```bash
# Development
npm run dev              # Start all services with Grok & Source editor
npm run dev:backend      # Start backend with plugin system
npm run dev:frontend     # Start frontend with enhanced UI
npm run dev:electron     # Start Electron with Tailscale integration

# Building
npm run build            # Build entire application
npm run build:frontend   # Build frontend with Monaco editor
npm run build:backend    # Build backend with plugins

# Production
npm start                # Start built application
npm run start:backend    # Start backend production server
npm run start:frontend   # Start frontend preview server

# Maintenance
npm run clean            # Clean build artifacts
npm run lint             # Run linters
npm run test             # Run tests

# Electron Distribution
npm run electron:build   # Build Electron app with Tailscale
npm run electron:dist    # Create distribution packages

# Enhanced Launcher
./launch-gremlin-trader.sh  # Launch complete system with all features
```

## 📊 Logging

### Backend Logging
- Configured with Python's `logging` module
- Logs written to `/tmp/gremlin_trader.log` and console
- Structured logging with timestamps and log levels
- Plugin-specific logging with `plugin.{name}` namespace

### Frontend Logging
- Custom TypeScript logger with multiple levels
- Console output and in-memory log storage
- Automatic log level adjustment for development/production
- Component-specific logging for debugging

### Electron Logging
- Main process logging for system events
- Renderer process logs forwarded to main process
- Error tracking and crash reporting
- Tailscale integration logging

## 🌐 PWA & Mobile Features

### Tailscale Integration
- Secure tunnel publishing for remote access
- QR code generation for mobile installation
- Cross-platform mobile PWA support
- Offline caching for core functionality

### Mobile Optimization
- Responsive design for all screen sizes
- Touch-friendly interface elements
- Optimized performance for mobile devices
- Progressive Web App capabilities

## 🐛 Troubleshooting

### Common Issues

#### Grok API Not Working
```bash
# Check API key configuration
nano backend/Gremlin_Trade_Core/config/FullSpec.config
# Ensure grok.api_key is set
```

#### Monaco Editor Not Loading
```bash
# Reinstall Monaco dependencies
cd frontend
npm install @monaco-editor/react
npm run build
```

#### Port Already in Use
```bash
# Kill processes using ports 8000 or 4321
lsof -ti:8000 | xargs kill -9
lsof -ti:4321 | xargs kill -9
```

#### Plugin System Issues
```bash
# Check plugin status
curl http://localhost:8000/api/plugins
# Restart backend to reload plugins
```

#### Tailscale Integration
```bash
# Check Tailscale status
tailscale status
# Restart Tailscale if needed
sudo tailscale up
```

#### Poetry Installation Issues
```bash
# Reinstall Poetry
curl -sSL https://install-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

#### Node.js Version Issues
```bash
# Use Node Version Manager (nvm)
nvm install 18
nvm use 18
```

## 🚀 Advanced Features

### Plugin Development
Create custom plugins by extending the `BasePlugin` class and registering them with the plugin manager.

### AI Integration
The Grok plugin supports both real API integration (with API key) and mock responses for development.

### Remote Access
Use Tailscale to securely access your trading dashboard from anywhere with mobile PWA support.

### Source Code Editing
Edit any file in the project directly from the web interface with syntax highlighting and auto-save.

## 📄 License

This project is licensed under the MIT License.

## 🏢 Company

**StatikFintech LLC**
- GitHub: [@statikfintechllc](https://github.com/statikfintechllc)

---

**Happy Trading with Grok AI!** 📈🤖🚀