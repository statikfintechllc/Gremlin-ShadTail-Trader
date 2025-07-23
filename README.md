# Gremlin ShadTail Trader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![Electron](https://img.shields.io/badge/Electron-27+-blueviolet.svg)](https://www.electronjs.org/)

GremlinGPT's standalone trading core designed as a comprehensive, AI-powered trading platform. This application serves as both a standalone desktop application and a foundation for VSCode plugin integration.

## 🚀 Overview

Gremlin ShadTail Trader combines modern web technologies with powerful backend processing to deliver a seamless trading experience:

- **Real-time Trading Dashboard** - Monitor market data and trading signals
- **AI-Powered Analysis** - Leverage GremlinGPT's trading intelligence
- **Cross-Platform Desktop App** - Built with Electron for Windows, macOS, and Linux
- **Modern Web Interface** - Responsive UI built with Astro, React, and Tailwind CSS
- **High-Performance Backend** - FastAPI-powered REST API with WebSocket support
- **Vector Memory System** - Advanced memory management for trading strategies

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
    │  Main   │              │  UI     │              │  API    │
    │ Process │              │ Layer   │              │ Routes  │
    └─────────┘              └─────────┘              └─────────┘
```

### Technology Stack

- **Frontend**: Astro 4.0, React 18, Tailwind CSS 3.4
- **Backend**: FastAPI, Python 3.11+, Uvicorn
- **Desktop**: Electron 27
- **Build Tools**: Vite, PostCSS, Autoprefixer
- **Package Management**: npm (frontend), Poetry (backend)
- **Development**: Hot reload, TypeScript support

## 📁 Directory Structure

```
gremlin-shadtail-trader/
├── backend/                    # FastAPI backend application
│   ├── Gremlin-Trade-Core/    # Core trading logic
│   ├── Gremlin-Trade-Memory/  # Vector memory system
│   ├── server.py              # Main FastAPI application
│   └── pyproject.toml         # Python dependencies
├── frontend/                   # Astro frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   │   └── Dashboard.tsx  # Main dashboard component
│   │   ├── pages/            # Astro pages
│   │   │   └── index.astro   # Landing page
│   │   └── utils/            # Utility functions
│   │       └── logger.ts     # Frontend logging system
│   ├── astro.config.mjs      # Astro configuration
│   ├── tailwind.config.cjs   # Tailwind CSS configuration
│   └── package.json          # Frontend dependencies
├── electron/                  # Electron main process
│   ├── main.js               # Main Electron process
│   └── preload.js            # Preload script for IPC
├── scripts/                   # Build and utility scripts
│   └── install-all           # Dependency installation script
├── package.json              # Root package.json (monorepo)
└── README.md                 # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- **Node.js 18+** - [Download here](https://nodejs.org/)
- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Poetry** - [Installation guide](https://python-poetry.org/docs/#installation)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/statikfintechllc/Gremlin-ShadTail-Trader.git
   cd Gremlin-ShadTail-Trader
   ```

2. **Install all dependencies**
   ```bash
   ./scripts/install-all
   # or
   npm run install-all
   ```

3. **Start development environment**
   ```bash
   npm run dev
   ```

This will start:
- Backend API server on `http://localhost:8000`
- Frontend dev server on `http://localhost:4321`
- Electron desktop application

### Manual Setup

If you prefer to set up each component manually:

#### Backend Setup
```bash
cd backend
poetry install --no-root
poetry run uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Electron Setup
```bash
npm install
npm run dev:electron
```

## 🎯 Usage

### Development Mode

Start all services in development mode:
```bash
npm run dev
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

### Trading Feed
- **GET** `/api/feed` - Get current trading data
- **WebSocket** `/ws/updates` - Real-time updates

### Settings Management
- **GET** `/api/settings` - Get current settings
- **POST** `/api/settings` - Update settings

### Memory System
- **GET** `/api/memory?q={query}` - Query vector memory store

### Example Usage

```javascript
// Fetch trading feed
const response = await fetch('http://localhost:8000/api/feed');
const data = await response.json();
// Returns: [{"symbol":"GPRO","price":2.15,"up_pct":112.0}]

// Update settings
await fetch('http://localhost:8000/api/settings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    scanInterval: 300,
    symbols: ['AAPL', 'MSFT', 'GOOGL']
  })
});
```

## 🎛️ UI Features

### Dashboard Components

- **Trading Feed Display** - Real-time market data with color-coded performance
- **Settings Panel** - Configure scan intervals and symbol watchlists
- **Responsive Design** - Adapts to different screen sizes
- **Dark Theme** - Modern dark interface optimized for trading

### Interaction Features

- **Live Data Updates** - Automatic refresh based on scan interval
- **Symbol Management** - Add/remove symbols from watchlist
- **Error Handling** - Graceful error display and recovery
- **Loading States** - Visual feedback during data fetching

## 🔧 Development

### Project Scripts

```bash
# Development
npm run dev              # Start all services
npm run dev:backend      # Start backend only
npm run dev:frontend     # Start frontend only
npm run dev:electron     # Start Electron only

# Building
npm run build            # Build entire application
npm run build:frontend   # Build frontend only
npm run build:backend    # Build backend only

# Production
npm start                # Start built application
npm run start:backend    # Start backend production server
npm run start:frontend   # Start frontend preview server

# Maintenance
npm run clean            # Clean build artifacts
npm run lint             # Run linters
npm run test             # Run tests

# Electron Distribution
npm run electron:build   # Build Electron app
npm run electron:dist    # Create distribution packages
```

## 📊 Logging

### Backend Logging
- Configured with Python's `logging` module
- Logs written to `/tmp/gremlin_trader.log` and console
- Structured logging with timestamps and log levels

### Frontend Logging
- Custom TypeScript logger with multiple levels
- Console output and in-memory log storage
- Automatic log level adjustment for development/production

### Electron Logging
- Main process logging for system events
- Renderer process logs forwarded to main process
- Error tracking and crash reporting

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill processes using ports 8000 or 4321
lsof -ti:8000 | xargs kill -9
lsof -ti:4321 | xargs kill -9
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

## 📄 License

This project is licensed under the MIT License.

## 🏢 Company

**StatikFintech LLC**
- GitHub: [@statikfintechllc](https://github.com/statikfintechllc)

---

**Happy Trading!** 📈🚀