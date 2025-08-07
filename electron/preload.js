const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Backend control
  restartBackend: () => ipcRenderer.invoke('restart-backend'),
  
  // Backend health monitoring
  checkBackendHealth: () => ipcRenderer.invoke('check-backend-health'),
  checkBackendBasic: () => ipcRenderer.invoke('check-backend-basic'),
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  
  // Tailscale control
  tailscaleStatus: () => ipcRenderer.invoke('tailscale-status'),
  tailscaleStart: (authKey) => ipcRenderer.invoke('tailscale-start', authKey),
  tailscaleStop: () => ipcRenderer.invoke('tailscale-stop'),
  tailscaleQRCode: () => ipcRenderer.invoke('tailscale-qr-code'),
  
  // Configuration
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  
  // File system access for Monaco editor
  getProjectFiles: () => ipcRenderer.invoke('get-project-files'),
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
  
  // Logging (send logs to main process)
  logToMain: (level, message, data) => {
    ipcRenderer.send('log-message', { level, message, data, timestamp: new Date().toISOString() });
  },
  
  // Platform info
  platform: process.platform,
  
  // Environment
  isDev: process.env.NODE_ENV === 'development',
});

// Window controls (optional)
contextBridge.exposeInMainWorld('windowAPI', {
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
});

// Enhanced logging for Electron environment
window.addEventListener('DOMContentLoaded', () => {
  // Override console methods to also send to main process
  const originalConsole = {
    log: console.log,
    info: console.info,
    warn: console.warn,
    error: console.error,
    debug: console.debug,
  };

  ['log', 'info', 'warn', 'error', 'debug'].forEach(method => {
    console[method] = (...args) => {
      // Call original console method
      originalConsole[method](...args);
      
      // Send to main process for logging
      if (window.electronAPI) {
        window.electronAPI.logToMain(method, args.join(' '));
      }
    };
  });
});

// Global error handlers
window.addEventListener('error', (event) => {
  if (window.electronAPI) {
    window.electronAPI.logToMain('error', `Global error: ${event.error.message}`, {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      stack: event.error.stack
    });
  }
});

window.addEventListener('unhandledrejection', (event) => {
  if (window.electronAPI) {
    window.electronAPI.logToMain('error', `Unhandled promise rejection: ${event.reason}`, {
      reason: event.reason
    });
  }
});