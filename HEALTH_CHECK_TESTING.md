# Backend Health Check System - Manual Testing Guide

This guide demonstrates the implemented backend health check system and Electron-backend communication fixes.

## 🚀 Quick Start Test

### 1. Start Backend Server
```bash
cd backend
python server.py
```

Expected output: Server starts with agent import validation

### 2. Test Health Endpoints

**Basic Health Check:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}
```

**Comprehensive Health Check:**
```bash
curl http://localhost:8000/api/system/health | jq
```

Expected output shows:
- System status: "degraded" (due to optional missing dependencies)
- Health score: 60+ (acceptable for operation) 
- Agent imports: 10/14 successful (71.4% success rate)
- Detailed status of each agent import

### 3. Test Backend Restart Scenario

**Kill Backend:**
```bash
pkill -f "python server.py"
```

**Verify Connection Error:**
```bash
curl http://localhost:8000/health
# Expected: Connection refused
```

**Restart Backend:**
```bash
cd backend && python server.py
```

**Verify Recovery:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}
```

## 🧪 Automated E2E Test

Run the comprehensive test suite:
```bash
python test_e2e_backend.py
```

This tests:
- ✅ Basic health endpoint
- ✅ Comprehensive health validation
- ✅ Backend restart scenario
- ✅ Error handling when backend is down

Expected: 4/4 tests pass

## 🖥️ Electron Integration

The Electron app now properly:

1. **Detects Backend Health**: Uses comprehensive health checks instead of basic ping
2. **Handles Degraded State**: Allows operation with 71.4% agent success rate
3. **Provides User Feedback**: Shows detailed error dialogs with agent status
4. **Supports Recovery**: Can restart backend and wait for full initialization

### Key IPC Functions Available to Frontend:

```javascript
// Check backend health status
window.electronAPI.checkBackendHealth()

// Get basic backend connection status  
window.electronAPI.checkBackendBasic()

// Get detailed backend system status
window.electronAPI.getBackendStatus()

// Restart backend and wait for it to be ready
window.electronAPI.restartAndWaitBackend()
```

## 🔧 System Configuration

The health check system is configured to:

- **Run in all modes**: No longer gated by `isDev`
- **Allow degraded operation**: Up to 30% agent failures acceptable
- **Provide detailed feedback**: Health scores, agent status, error reasons
- **Support graceful recovery**: Clean restart and reconnection

## 📊 Health Status Levels

1. **Healthy** (100 score): All agents imported successfully
2. **Degraded** (50-90 score): Some agents failed but system operational  
3. **Unhealthy** (0-49 score): Too many failures, limited functionality

Current typical status with minimal dependencies: **Degraded (60 score, 10/14 agents)**

This is acceptable for basic trading system operation.