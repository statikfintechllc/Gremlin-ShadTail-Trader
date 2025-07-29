#!/usr/bin/env node

/**
 * Post-pack script for Electron Builder
 * Ensures packaged app has correct permissions and runtime files
 */

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

function log(message) {
    console.log(`[POSTPACK] ${new Date().toISOString()} ${message}`);
}

async function execAsync(command, options = {}) {
    return new Promise((resolve, reject) => {
        exec(command, options, (error, stdout, stderr) => {
            if (error) {
                log(`Warning: ${command} failed: ${error.message}`);
                resolve(''); // Don't fail the build for post-pack issues
            } else {
                resolve(stdout);
            }
        });
    });
}

async function postpack(context) {
    try {
        log('Starting post-pack process...');
        
        const { electronPlatformName, appOutDir } = context;
        log(`Platform: ${electronPlatformName}`);
        log(`Output directory: ${appOutDir}`);
        
        if (electronPlatformName === 'darwin') {
            await postpackMac(appOutDir);
        } else if (electronPlatformName === 'win32') {
            await postpackWindows(appOutDir);
        } else if (electronPlatformName === 'linux') {
            await postpackLinux(appOutDir);
        }
        
        log('Post-pack completed successfully');
        
    } catch (error) {
        log(`Post-pack warning: ${error.message}`);
        // Don't fail the build for post-pack issues
    }
}

async function postpackMac(appOutDir) {
    log('Post-processing macOS app...');
    
    const appPath = path.join(appOutDir, 'Gremlin ShadTail Trader.app');
    const contentsPath = path.join(appPath, 'Contents');
    const resourcesPath = path.join(contentsPath, 'Resources');
    
    // Ensure bootstrap script is executable
    const bootstrapPath = path.join(resourcesPath, 'scripts', 'bootstrap.js');
    if (fs.existsSync(bootstrapPath)) {
        await execAsync(`chmod +x "${bootstrapPath}"`);
        log('Made bootstrap script executable');
    }
    
    // Fix Python backend permissions
    const backendPath = path.join(resourcesPath, 'backend');
    if (fs.existsSync(backendPath)) {
        await execAsync(`find "${backendPath}" -name "*.py" -exec chmod +x {} \\;`);
        log('Fixed Python script permissions');
    }
    
    // Create symlinks for system Python if needed
    await createPythonSymlinks(resourcesPath);
}

async function postpackWindows(appOutDir) {
    log('Post-processing Windows app...');
    
    const resourcesPath = path.join(appOutDir, 'resources');
    
    // Ensure scripts have proper line endings
    const scriptsPath = path.join(resourcesPath, 'scripts');
    if (fs.existsSync(scriptsPath)) {
        const scripts = fs.readdirSync(scriptsPath).filter(f => f.endsWith('.js'));
        for (const script of scripts) {
            const scriptPath = path.join(scriptsPath, script);
            let content = fs.readFileSync(scriptPath, 'utf8');
            content = content.replace(/\r\n/g, '\n').replace(/\n/g, '\r\n');
            fs.writeFileSync(scriptPath, content);
        }
        log('Fixed script line endings for Windows');
    }
    
    // Create Python environment helper
    await createWindowsPythonHelper(resourcesPath);
}

async function postpackLinux(appOutDir) {
    log('Post-processing Linux app...');
    
    const resourcesPath = path.join(appOutDir, 'resources');
    
    // Ensure all scripts are executable
    const scriptsPath = path.join(resourcesPath, 'scripts');
    if (fs.existsSync(scriptsPath)) {
        await execAsync(`chmod +x "${scriptsPath}"/*.js`);
        log('Made scripts executable');
    }
    
    // Fix Python backend permissions
    const backendPath = path.join(resourcesPath, 'backend');
    if (fs.existsSync(backendPath)) {
        await execAsync(`find "${backendPath}" -name "*.py" -exec chmod +x {} \\;`);
        log('Fixed Python script permissions');
        
        // Install Poetry dependencies for the packaged backend
        log('Installing Poetry dependencies for packaged backend...');
        const poetryInstallResult = await execAsync(`cd "${backendPath}" && poetry install`);
        if (poetryInstallResult !== '') {
            log('Poetry dependencies installed successfully');
        } else {
            log('Poetry dependency installation completed');
        }
    }
    
    // Create desktop entry
    await createDesktopEntry(appOutDir);
}

async function createPythonSymlinks(resourcesPath) {
    // Create symlinks to help the app find Python and Poetry
    const binPath = path.join(resourcesPath, 'bin');
    if (!fs.existsSync(binPath)) {
        fs.mkdirSync(binPath, { recursive: true });
    }
    
    // Try to create symlinks to system Python
    try {
        const pythonPath = await execAsync('which python3');
        if (pythonPath.trim()) {
            const symlinkPath = path.join(binPath, 'python3');
            if (!fs.existsSync(symlinkPath)) {
                fs.symlinkSync(pythonPath.trim(), symlinkPath);
                log('Created Python3 symlink');
            }
        }
    } catch (error) {
        log('Could not create Python3 symlink');
    }
    
    try {
        const poetryPath = await execAsync('which poetry');
        if (poetryPath.trim()) {
            const symlinkPath = path.join(binPath, 'poetry');
            if (!fs.existsSync(symlinkPath)) {
                fs.symlinkSync(poetryPath.trim(), symlinkPath);
                log('Created Poetry symlink');
            }
        }
    } catch (error) {
        log('Could not create Poetry symlink');
    }
}

async function createWindowsPythonHelper(resourcesPath) {
    const helperScript = `@echo off
REM Python Environment Helper for Gremlin ShadTail Trader

REM Add common Python paths to PATH
set PATH=%PATH%;C:\\Python311\\Scripts;C:\\Python311;C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python311\\Scripts;C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python311

REM Add Poetry to PATH
set PATH=%PATH%;C:\\Users\\%USERNAME%\\AppData\\Roaming\\Python\\Scripts

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.11+ from https://python.org/
    pause
    exit /b 1
)

REM Check if Poetry is available
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Poetry not found. Installing Poetry...
    curl -sSL https://install.python-poetry.org | python -
    if %errorlevel% neq 0 (
        echo Failed to install Poetry. Please install manually from https://python-poetry.org/
        pause
        exit /b 1
    )
)

echo Python environment ready
`;
    
    const helperPath = path.join(resourcesPath, 'python-env.bat');
    fs.writeFileSync(helperPath, helperScript);
    log('Created Python environment helper for Windows');
}

async function createDesktopEntry(appOutDir) {
    const desktopEntry = `[Desktop Entry]
Version=1.0
Type=Application
Name=Gremlin ShadTail Trader
Comment=Autonomous Trading System with AI/ML
Exec=${path.join(appOutDir, 'gremlin-shadtail-trader')}
Icon=gremlin-shadtail-trader
Terminal=false
Categories=Office;Finance;
StartupWMClass=Gremlin ShadTail Trader
`;
    
    const desktopPath = path.join(appOutDir, 'gremlin-shadtail-trader.desktop');
    fs.writeFileSync(desktopPath, desktopEntry);
    await execAsync(`chmod +x "${desktopPath}"`);
    log('Created desktop entry');
}

module.exports = postpack;