#!/usr/bin/env node

/**
 * Universal Bootstrap Shell for Gremlin ShadTail Trader
 * Automatically detects environment and starts both Python backend and Electron frontend
 */

const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Configuration
const APP_NAME = 'Gremlin ShadTail Trader';
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 4321;
const STARTUP_TIMEOUT = 30000; // 30 seconds

// Colors for console output
const colors = {
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
    reset: '\x1b[0m'
};

function log(level, message) {
    const timestamp = new Date().toISOString();
    const color = colors[level] || colors.reset;
    console.log(`${color}[${timestamp}] [${level.toUpperCase()}] ${message}${colors.reset}`);
}

class GremlinBootstrap {
    constructor() {
        this.processes = new Map();
        this.isShuttingDown = false;
        this.platform = os.platform();
        this.projectRoot = path.dirname(__dirname);
        
        // Bind methods
        this.cleanup = this.cleanup.bind(this);
        this.handleSignal = this.handleSignal.bind(this);
        
        // Setup signal handlers
        process.on('SIGINT', this.handleSignal);
        process.on('SIGTERM', this.handleSignal);
        process.on('exit', this.cleanup);
    }

    async start() {
        try {
            log('blue', `Starting ${APP_NAME}...`);
            log('blue', `Platform: ${this.platform}`);
            log('blue', `Project Root: ${this.projectRoot}`);
            
            // Check if dependencies are installed
            await this.checkDependencies();
            
            // Start Python backend daemon
            await this.startBackend();
            
            // Wait for backend to be ready
            await this.waitForBackend();
            
            // Start Electron frontend
            await this.startFrontend();
            
            log('green', `${APP_NAME} started successfully!`);
            log('green', `Backend running on http://localhost:${BACKEND_PORT}`);
            log('green', `Frontend will open automatically in Electron window`);
            
        } catch (error) {
            log('red', `Failed to start ${APP_NAME}: ${error.message}`);
            await this.cleanup();
            process.exit(1);
        }
    }

    async checkDependencies() {
        log('blue', 'Checking dependencies...');
        
        // Check Node.js
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
        if (majorVersion < 18) {
            throw new Error(`Node.js 18+ required, found ${nodeVersion}`);
        }
        log('green', `Node.js ${nodeVersion} ✓`);
        
        // Check Python
        try {
            await this.execAsync('python3 --version');
            log('green', 'Python 3 ✓');
        } catch (error) {
            throw new Error('Python 3 not found. Please install Python 3.11+');
        }
        
        // Check Poetry
        try {
            await this.execAsync('poetry --version');
            log('green', 'Poetry ✓');
        } catch (error) {
            log('yellow', 'Poetry not found, attempting to install...');
            await this.installPoetry();
        }
        
        // Check if npm dependencies are installed
        if (!fs.existsSync(path.join(this.projectRoot, 'node_modules'))) {
            log('yellow', 'Installing npm dependencies...');
            await this.execAsync('npm install', { cwd: this.projectRoot });
        }
        
        // Check if Python dependencies are installed
        const backendDir = path.join(this.projectRoot, 'backend');
        try {
            await this.execAsync('poetry check', { cwd: backendDir });
            log('green', 'Python dependencies ✓');
        } catch (error) {
            log('yellow', 'Installing Python dependencies...');
            await this.execAsync('poetry install --no-root', { cwd: backendDir });
        }
    }

    async installPoetry() {
        const installCmd = this.platform === 'win32' 
            ? 'powershell -Command "(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -"'
            : 'curl -sSL https://install.python-poetry.org | python3 -';
        
        await this.execAsync(installCmd);
        
        // Add Poetry to PATH
        const poetryPath = this.platform === 'win32'
            ? path.join(os.homedir(), 'AppData', 'Roaming', 'Python', 'Scripts')
            : path.join(os.homedir(), '.local', 'bin');
        
        process.env.PATH = `${poetryPath}${path.delimiter}${process.env.PATH}`;
        log('green', 'Poetry installed ✓');
    }

    async startBackend() {
        log('blue', 'Starting Python backend daemon...');
        
        const backendDir = path.join(this.projectRoot, 'backend');
        const backendCmd = 'poetry';
        const backendArgs = [
            'run', 'uvicorn', 
            'dashboard_backend.server:app',
            '--host', '0.0.0.0',
            '--port', BACKEND_PORT.toString(),
            '--log-level', 'info'
        ];
        
        const backendProcess = spawn(backendCmd, backendArgs, {
            cwd: backendDir,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
        });
        
        this.processes.set('backend', backendProcess);
        
        backendProcess.stdout.on('data', (data) => {
            const message = data.toString().trim();
            if (message) log('cyan', `[Backend] ${message}`);
        });
        
        backendProcess.stderr.on('data', (data) => {
            const message = data.toString().trim();
            if (message) log('yellow', `[Backend] ${message}`);
        });
        
        backendProcess.on('exit', (code) => {
            if (!this.isShuttingDown) {
                log('red', `Backend process exited with code ${code}`);
                this.cleanup();
                process.exit(1);
            }
        });
        
        log('green', 'Backend daemon started');
    }

    async waitForBackend() {
        log('blue', 'Waiting for backend to be ready...');
        
        const startTime = Date.now();
        while (Date.now() - startTime < STARTUP_TIMEOUT) {
            try {
                const response = await this.httpGet(`http://localhost:${BACKEND_PORT}/health`);
                if (response) {
                    log('green', 'Backend is ready ✓');
                    return;
                }
            } catch (error) {
                // Backend not ready yet, continue waiting
            }
            
            await this.sleep(1000);
        }
        
        throw new Error('Backend failed to start within timeout');
    }

    async startFrontend() {
        log('blue', 'Starting Electron frontend...');
        
        // Determine Electron command and arguments based on environment
        const electronCmd = 'electron';
        const electronArgs = [
            '.',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ];
        
        // Add display-specific arguments
        if (process.env.DISPLAY) {
            electronArgs.push(`--display=${process.env.DISPLAY}`);
        }
        
        // Check if running in headless environment
        if (this.isHeadless()) {
            log('yellow', 'Headless environment detected');
            electronArgs.push('--virtual-frame-buffer');
            
            // Try to start Xvfb if available
            try {
                await this.startXvfb();
            } catch (error) {
                log('yellow', 'Xvfb not available, continuing without virtual display');
            }
        }
        
        const frontendProcess = spawn(electronCmd, electronArgs, {
            cwd: this.projectRoot,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { 
                ...process.env, 
                NODE_ENV: 'production',
                BACKEND_URL: `http://localhost:${BACKEND_PORT}`
            }
        });
        
        this.processes.set('frontend', frontendProcess);
        
        frontendProcess.stdout.on('data', (data) => {
            const message = data.toString().trim();
            if (message) log('magenta', `[Frontend] ${message}`);
        });
        
        frontendProcess.stderr.on('data', (data) => {
            const message = data.toString().trim();
            if (message && !message.includes('GPU process')) {
                log('yellow', `[Frontend] ${message}`);
            }
        });
        
        frontendProcess.on('exit', (code) => {
            if (!this.isShuttingDown) {
                log('blue', `Frontend process exited with code ${code}`);
                this.cleanup();
                process.exit(0);
            }
        });
        
        log('green', 'Frontend started');
    }

    isHeadless() {
        return !process.env.DISPLAY && 
               (process.env.CI || 
                process.env.GITHUB_ACTIONS || 
                process.env.JENKINS_URL ||
                process.env.HEADLESS === 'true');
    }

    async startXvfb() {
        const xvfbProcess = spawn('Xvfb', [':99', '-screen', '0', '1024x768x24'], {
            stdio: 'ignore'
        });
        
        this.processes.set('xvfb', xvfbProcess);
        process.env.DISPLAY = ':99';
        
        await this.sleep(2000); // Give Xvfb time to start
        log('green', 'Xvfb virtual display started');
    }

    async httpGet(url) {
        return new Promise((resolve, reject) => {
            const protocol = url.startsWith('https:') ? require('https') : require('http');
            const request = protocol.get(url, (response) => {
                let data = '';
                response.on('data', chunk => data += chunk);
                response.on('end', () => {
                    if (response.statusCode === 200) {
                        resolve(data);
                    } else {
                        reject(new Error(`HTTP ${response.statusCode}`));
                    }
                });
            });
            request.on('error', reject);
            request.setTimeout(5000, () => {
                request.destroy();
                reject(new Error('Request timeout'));
            });
        });
    }

    async execAsync(command, options = {}) {
        return new Promise((resolve, reject) => {
            exec(command, options, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(stdout);
                }
            });
        });
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    handleSignal(signal) {
        log('yellow', `Received ${signal}, shutting down gracefully...`);
        this.cleanup();
        process.exit(0);
    }

    async cleanup() {
        if (this.isShuttingDown) return;
        this.isShuttingDown = true;
        
        log('blue', 'Shutting down processes...');
        
        for (const [name, process] of this.processes) {
            try {
                if (!process.killed) {
                    log('blue', `Stopping ${name}...`);
                    process.kill('SIGTERM');
                    
                    // Give process time to exit gracefully
                    await this.sleep(2000);
                    
                    if (!process.killed) {
                        log('yellow', `Force killing ${name}...`);
                        process.kill('SIGKILL');
                    }
                }
            } catch (error) {
                log('yellow', `Error stopping ${name}: ${error.message}`);
            }
        }
        
        this.processes.clear();
        log('green', 'Cleanup complete');
    }
}

// Main execution
if (require.main === module) {
    const bootstrap = new GremlinBootstrap();
    bootstrap.start().catch((error) => {
        log('red', `Bootstrap failed: ${error.message}`);
        process.exit(1);
    });
}

module.exports = GremlinBootstrap;