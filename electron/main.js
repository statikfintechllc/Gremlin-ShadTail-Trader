stock_scraper.py
backend/Gremlin_Trade_Core/Gremlin_Trader_Tools/Run_Time_Agent/stock_scraper.py
backend/Gremlin_Trade_Core/Gremlin_Trader_Tools/Run_Time_Agent/stock_scraper.py
const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;
let backendProcess;
let frontendProcess;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false, // Allow localhost connections in dev
    },
    icon: path.join(__dirname, '../assets/icon.png'), // Add icon if available
    titleBarStyle: 'default',
    show: false, // Don't show until ready
  });

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Load the frontend
  if (isDev) {
    // In development, use the Astro dev server
    mainWindow.loadURL('http://localhost:4321');
  } else {
    // In production, load the built files
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  console.log('Starting backend server...');
  
  const backendPath = path.join(__dirname, '../backend');
  
  // Start the FastAPI backend using poetry or uvicorn
  backendProcess = spawn('poetry', ['run', 'uvicorn', 'server:app', '--host', '0.0.0.0', '--port', '8000'], {
    cwd: backendPath,
    stdio: 'pipe',
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

function startFrontend() {
  if (!isDev) return; // Only start dev server in development
  
  console.log('Starting frontend dev server...');
  
  const frontendPath = path.join(__dirname, '../frontend');
  
  frontendProcess = spawn('npm', ['run', 'dev'], {
    cwd: frontendPath,
    stdio: 'pipe',
  });

  frontendProcess.stdout.on('data', (data) => {
    console.log(`Frontend: ${data}`);
  });

  frontendProcess.stderr.on('data', (data) => {
    console.error(`Frontend Error: ${data}`);
  });

  frontendProcess.on('close', (code) => {
    console.log(`Frontend process exited with code ${code}`);
  });
}

function stopProcesses() {
  console.log('Stopping processes...');
  
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  
  if (frontendProcess) {
    frontendProcess.kill();
    frontendProcess = null;
  }
}

// App event handlers
app.whenReady().then(() => {
  // Start backend first
  startBackend();
  
  // Start frontend dev server if in development
  if (isDev) {
    startFrontend();
    
    // Wait for servers to start before creating window
    setTimeout(() => {
      createWindow();
    }, 3000);
  } else {
    // In production, create window immediately
    setTimeout(() => {
      createWindow();
    }, 2000);
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopProcesses();
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopProcesses();
});

// IPC handlers for communication with renderer process
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('restart-backend', () => {
  stopProcesses();
  setTimeout(() => {
    startBackend();
  }, 1000);
  return 'Backend restart initiated';
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  stopProcesses();
  app.quit();
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});