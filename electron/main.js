const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');

// Auto-detect if we need to disable sandbox based on environment
const needsSandboxDisabled = () => {
  // Check if we're running in a container or CI environment
  if (process.env.DOCKER_CONTAINER || 
      process.env.CI || 
      process.env.GITHUB_ACTIONS ||
      process.env.container ||
      fs.existsSync('/.dockerenv')) {
    return true;
  }
  
  // Check if chrome-sandbox exists and has proper permissions
  try {
    const sandboxPath = path.join(__dirname, '../node_modules/electron/dist/chrome-sandbox');
    if (fs.existsSync(sandboxPath)) {
      const stats = fs.statSync(sandboxPath);
      // Check if sandbox binary has proper SUID permissions (mode 4755)
      const expectedMode = parseInt('4755', 8);
      if ((stats.mode & parseInt('7777', 8)) !== expectedMode) {
        return true;
      }
    }
  } catch (error) {
    // If we can't check the sandbox, it's safer to disable it
    return true;
  }
  
  return false;
};

// COMPLETELY DISABLE ALL SANDBOXING - NO CONSTRAINTS
console.log('Disabling Electron sandbox due to environment constraints');
app.commandLine.appendSwitch('--no-sandbox');
app.commandLine.appendSwitch('--disable-dev-shm-usage');
app.commandLine.appendSwitch('--disable-gpu');
app.commandLine.appendSwitch('--disable-features=VizDisplayCompositor');
app.commandLine.appendSwitch('--disable-web-security');
app.commandLine.appendSwitch('--allow-running-insecure-content');
app.commandLine.appendSwitch('--disable-background-timer-throttling');
app.commandLine.appendSwitch('--disable-backgrounding-occluded-windows');
app.commandLine.appendSwitch('--disable-renderer-backgrounding');

const isDev = process.env.NODE_ENV === 'development';

let mainWindow;
let backendProcess;
let frontendProcess;
let tailscaleStatus = { connected: false, ip: null, hostname: null };

function createWindow() {
  // Create the browser window with NO CONSTRAINTS
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    backgroundColor: '#000000', // Dark background
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true,
      webSecurity: false,
      allowRunningInsecureContent: true,
      experimentalFeatures: true,
    },
    icon: path.join(__dirname, '../resources/icon.png'),
    titleBarStyle: 'default',
    show: false,
    frame: true,
    resizable: true,
    maximizable: true,
    minimizable: true,
    closable: true,
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
    // In production, load the built files from inside the asar package
    const frontendPath = path.join(__dirname, '../frontend/dist/index.html');
    console.log('Looking for frontend at:', frontendPath);
    
    if (fs.existsSync(frontendPath)) {
      console.log('Loading frontend from:', frontendPath);
      mainWindow.loadFile(frontendPath);
    } else {
      console.error('Frontend build files not found at:', frontendPath);
      console.log('__dirname:', __dirname);
      console.log('Available files:', fs.readdirSync(path.join(__dirname, '..')));
      
      // Fallback: try different path
      const fallbackPath = path.join(__dirname, '../frontend-dist/index.html');
      if (fs.existsSync(fallbackPath)) {
        console.log('Loading frontend from fallback:', fallbackPath);
        mainWindow.loadFile(fallbackPath);
      } else {
        console.error('Frontend build files not found. Please run "npm run build" first.');
        app.quit();
        return;
      }
    }
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  console.log('Starting backend server...');
  
  let backendPath, command, args;
  
  if (isDev) {
    // Development mode - use poetry
    backendPath = path.join(__dirname, '../backend');
    command = 'poetry';
    args = ['run', 'uvicorn', 'server:app', '--host', '0.0.0.0', '--port', '8000'];
  } else {
    // Production mode - check multiple possible locations for backend
    const possibleBackendPaths = [
      path.join(process.resourcesPath, 'backend'),
      path.join(__dirname, '../backend'),
      path.join(__dirname, '../resources/backend'),
      path.join(process.cwd(), 'backend')
    ];
    
    backendPath = possibleBackendPaths.find(p => fs.existsSync(p));
    
    if (!backendPath) {
      console.error('Backend not found in any expected location:', possibleBackendPaths);
      return;
    }
    
    console.log('Using backend path:', backendPath);
    
    // Check if Poetry is available first, fallback to direct Python
    let usePoetry = false;
    try {
      require('child_process').execSync('poetry --version', { stdio: 'ignore' });
      usePoetry = true;
      console.log('Poetry available, using Poetry mode');
    } catch {
      console.log('Poetry not available, using direct Python mode');
    }
    
    if (usePoetry) {
      // Use Poetry if available (better for development/local builds)
      command = 'poetry';
      args = ['run', 'uvicorn', 'server:app', '--host', '0.0.0.0', '--port', '8000'];
    } else {
      // Direct Python mode for true production builds
      const pythonExecutables = [
        'python3',
        'python',
        '/usr/bin/python3',
        '/usr/bin/python'
      ];
      
      command = pythonExecutables.find(p => {
        try {
          require('child_process').execSync(`which ${p}`, { stdio: 'ignore' });
          return true;
        } catch {
          return false;
        }
      }) || 'python3';
      
      args = ['-m', 'uvicorn', 'server:app', '--host', '0.0.0.0', '--port', '8000'];
      
      // Set comprehensive PYTHONPATH for production
      const pythonPaths = [
        backendPath,
        path.join(backendPath, 'Gremlin_Trade_Core'),
        path.join(backendPath, 'Gremlin_Trade_Memory'),
        process.env.PYTHONPATH || ''
      ].filter(Boolean);
      
      process.env.PYTHONPATH = pythonPaths.join(':');
    }
  }

  console.log(`Backend path: ${backendPath}`);
  console.log(`Command: ${command} ${args.join(' ')}`);

  // Check if backend path exists
  if (!fs.existsSync(backendPath)) {
    console.error(`Backend path does not exist: ${backendPath}`);
    return;
  }

  backendProcess = spawn(command, args, {
    cwd: backendPath,
    stdio: 'pipe',
    env: process.env
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

  backendProcess.on('error', (error) => {
    console.error(`Backend spawn error: ${error.message}`);
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

// Tailscale Management Functions
async function checkTailscaleStatus() {
  return new Promise((resolve) => {
    exec('tailscale status --json', (error, stdout, stderr) => {
      if (error) {
        console.log('Tailscale not available or not running');
        tailscaleStatus = { connected: false, ip: null, hostname: null };
        resolve(tailscaleStatus);
        return;
      }
      
      try {
        const status = JSON.parse(stdout);
        tailscaleStatus = {
          connected: status.BackendState === 'Running',
          ip: status.TailscaleIPs && status.TailscaleIPs[0],
          hostname: status.Self && status.Self.HostName
        };
        console.log('Tailscale status:', tailscaleStatus);
        resolve(tailscaleStatus);
      } catch (parseError) {
        console.error('Failed to parse Tailscale status:', parseError);
        tailscaleStatus = { connected: false, ip: null, hostname: null };
        resolve(tailscaleStatus);
      }
    });
  });
}

async function startTailscale(authKey = null) {
  return new Promise((resolve, reject) => {
    const command = authKey ? `tailscale up --auth-key=${authKey}` : 'tailscale up';
    
    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error('Failed to start Tailscale:', error);
        reject(error);
        return;
      }
      
      console.log('Tailscale started:', stdout);
      setTimeout(() => {
        checkTailscaleStatus().then(resolve);
      }, 2000);
    });
  });
}

async function stopTailscale() {
  return new Promise((resolve, reject) => {
    exec('tailscale down', (error, stdout, stderr) => {
      if (error) {
        console.error('Failed to stop Tailscale:', error);
        reject(error);
        return;
      }
      
      console.log('Tailscale stopped:', stdout);
      tailscaleStatus = { connected: false, ip: null, hostname: null };
      resolve(tailscaleStatus);
    });
  });
}

async function getTailscaleQRCode() {
  return new Promise((resolve, reject) => {
    exec('tailscale web --auth-key --json', (error, stdout, stderr) => {
      if (error) {
        console.error('Failed to get Tailscale web URL:', error);
        reject(error);
        return;
      }
      
      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (parseError) {
        console.error('Failed to parse Tailscale web result:', parseError);
        reject(parseError);
      }
    });
  });
}

function loadFullSpecConfig() {
  try {
    const configPath = path.join(__dirname, '../backend/Gremlin_Trade_Core/config/FullSpec.config');
    if (fs.existsSync(configPath)) {
      const configData = fs.readFileSync(configPath, 'utf8');
      return JSON.parse(configData);
    }
  } catch (error) {
    console.error('Failed to load FullSpec config:', error);
  }
  return null;
}

// App event handlers
app.whenReady().then(async () => {
  // Check Tailscale status first
  await checkTailscaleStatus();
  
  // Auto-start Tailscale if configured
  const config = loadFullSpecConfig();
  if (config && config.system_config && config.system_config.enable_tailscale_tunnel) {
    console.log('Auto-starting Tailscale...');
    try {
      const authKey = config.other_logins?.tailscale?.auth_key;
      await startTailscale(authKey);
    } catch (error) {
      console.warn('Failed to auto-start Tailscale:', error);
    }
  }
  
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
}); // Close the app.whenReady().then() function

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

// File system access for Monaco editor
ipcMain.handle('get-project-files', async () => {
  try {
    const projectRoot = path.join(__dirname, '..');
    const files = await getDirectoryTree(projectRoot);
    return { success: true, files };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const projectRoot = path.join(__dirname, '..');
    const fullPath = path.resolve(projectRoot, filePath);
    
    // Security check - ensure file is within project
    if (!fullPath.startsWith(projectRoot)) {
      throw new Error('Access denied: File outside project directory');
    }
    
    const content = fs.readFileSync(fullPath, 'utf8');
    return { success: true, content };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('write-file', async (event, filePath, content) => {
  try {
    const projectRoot = path.join(__dirname, '..');
    const fullPath = path.resolve(projectRoot, filePath);
    
    // Security check - ensure file is within project
    if (!fullPath.startsWith(projectRoot)) {
      throw new Error('Access denied: File outside project directory');
    }
    
    // Ensure directory exists
    const dir = path.dirname(fullPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(fullPath, content, 'utf8');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

async function getDirectoryTree(dirPath, basePath = '') {
  const items = [];
  const files = fs.readdirSync(dirPath);
  
  for (const file of files) {
    // Skip hidden files and node_modules
    if (file.startsWith('.') || file === 'node_modules' || file === '__pycache__') {
      continue;
    }
    
    const fullPath = path.join(dirPath, file);
    const relativePath = path.join(basePath, file);
    const stats = fs.statSync(fullPath);
    
    if (stats.isDirectory()) {
      const children = await getDirectoryTree(fullPath, relativePath);
      items.push({
        name: file,
        path: relativePath,
        type: 'directory',
        children: children
      });
    } else {
      items.push({
        name: file,
        path: relativePath,
        type: 'file',
        size: stats.size,
        modified: stats.mtime.toISOString()
      });
    }
  }
  
  return items.sort((a, b) => {
    // Directories first, then files
    if (a.type === 'directory' && b.type === 'file') return -1;
    if (a.type === 'file' && b.type === 'directory') return 1;
    return a.name.localeCompare(b.name);
  });
}

ipcMain.handle('restart-backend', () => {
  stopProcesses();
  setTimeout(() => {
    startBackend();
  }, 1000);
  return 'Backend restart initiated';
});

// Tailscale IPC handlers
ipcMain.handle('tailscale-status', async () => {
  return await checkTailscaleStatus();
});

ipcMain.handle('tailscale-start', async (event, authKey) => {
  try {
    return await startTailscale(authKey);
  } catch (error) {
    throw new Error(`Failed to start Tailscale: ${error.message}`);
  }
});

ipcMain.handle('tailscale-stop', async () => {
  try {
    return await stopTailscale();
  } catch (error) {
    throw new Error(`Failed to stop Tailscale: ${error.message}`);
  }
});

ipcMain.handle('tailscale-qr-code', async () => {
  try {
    return await getTailscaleQRCode();
  } catch (error) {
    throw new Error(`Failed to get QR code: ${error.message}`);
  }
});

ipcMain.handle('get-config', () => {
  return loadFullSpecConfig();
});

ipcMain.handle('save-config', (event, config) => {
  try {
    const configPath = path.join(__dirname, '../backend/Gremlin_Trade_Core/config/FullSpec.config');
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    return { success: true };
  } catch (error) {
    throw new Error(`Failed to save config: ${error.message}`);
  }
}); // Added missing closing brace

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  stopProcesses();
  app.quit();
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});