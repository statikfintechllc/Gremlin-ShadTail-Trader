#!/usr/bin/env node

/**
 * Pre-build script for Electron Builder
 * Ensures all dependencies are built and resources are prepared
 */

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

function log(message) {
    console.log(`[PREBUILD] ${new Date().toISOString()} ${message}`);
}

async function execAsync(command, options = {}) {
    return new Promise((resolve, reject) => {
        exec(command, options, (error, stdout, stderr) => {
            if (error) {
                reject(new Error(`${command} failed: ${error.message}\n${stderr}`));
            } else {
                resolve(stdout);
            }
        });
    });
}

async function prebuild() {
    try {
        log('Starting pre-build process...');
        
        const projectRoot = path.dirname(__dirname);
        
        // Ensure frontend is built
        log('Building frontend...');
        const frontendDir = path.join(projectRoot, 'frontend');
        if (fs.existsSync(frontendDir)) {
            await execAsync('npm run build', { cwd: frontendDir });
            log('Frontend built successfully');
        } else {
            log('Warning: Frontend directory not found');
        }
        
        // Ensure backend is built
        log('Building backend...');
        const backendDir = path.join(projectRoot, 'backend');
        if (fs.existsSync(path.join(backendDir, 'pyproject.toml'))) {
            try {
                await execAsync('poetry build', { cwd: backendDir });
                log('Backend built successfully');
            } catch (error) {
                log('Warning: Backend build failed, continuing...');
            }
        } else {
            log('Warning: Backend pyproject.toml not found');
        }
        
        // Create resources directory if it doesn't exist
        const resourcesDir = path.join(projectRoot, 'resources');
        if (!fs.existsSync(resourcesDir)) {
            fs.mkdirSync(resourcesDir, { recursive: true });
            log('Created resources directory');
        }
        
        // Create default icon if it doesn't exist
        await createDefaultIcons(resourcesDir);
        
        // Copy scripts to ensure they're available in packaged app
        const scriptsDir = path.join(projectRoot, 'scripts');
        const targetScriptsDir = path.join(projectRoot, 'dist-scripts');
        if (fs.existsSync(scriptsDir)) {
            if (fs.existsSync(targetScriptsDir)) {
                fs.rmSync(targetScriptsDir, { recursive: true, force: true });
            }
            fs.cpSync(scriptsDir, targetScriptsDir, { recursive: true });
            log('Scripts copied for packaging');
        }
        
        log('Pre-build completed successfully');
        
    } catch (error) {
        console.error(`Pre-build failed: ${error.message}`);
        process.exit(1);
    }
}

async function createDefaultIcons(resourcesDir) {
    const iconFiles = [
        { name: 'icon.png', size: 512 },
        { name: 'icon.ico', format: 'ico' },
        { name: 'icon.icns', format: 'icns' }
    ];
    
    for (const iconFile of iconFiles) {
        const iconPath = path.join(resourcesDir, iconFile.name);
        if (!fs.existsSync(iconPath)) {
            // Create a simple text-based icon placeholder
            await createPlaceholderIcon(iconPath, iconFile);
            log(`Created placeholder icon: ${iconFile.name}`);
        }
    }
    
    // Create DMG background if it doesn't exist
    const dmgBgPath = path.join(resourcesDir, 'dmg-background.png');
    if (!fs.existsSync(dmgBgPath)) {
        await createDMGBackground(dmgBgPath);
        log('Created DMG background');
    }
    
    // Create entitlements file for macOS
    const entitlementsPath = path.join(resourcesDir, 'entitlements.mac.plist');
    if (!fs.existsSync(entitlementsPath)) {
        await createEntitlements(entitlementsPath);
        log('Created macOS entitlements');
    }
}

async function createPlaceholderIcon(iconPath, iconInfo) {
    // Create a simple SVG that can be converted to different formats
    const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" fill="#1a1a2e" rx="64"/>
  <circle cx="256" cy="180" r="80" fill="#16213e" stroke="#0f3460" stroke-width="4"/>
  <path d="M180 280 L256 320 L332 280 L332 380 L180 380 Z" fill="#e94560" stroke="#0f3460" stroke-width="2"/>
  <text x="256" y="450" text-anchor="middle" fill="#eee" font-family="Arial, sans-serif" font-size="24" font-weight="bold">GREMLIN</text>
</svg>`;
    
    if (iconInfo.name.endsWith('.png')) {
        // For PNG, we'll save the SVG (most systems can handle SVG as PNG)
        fs.writeFileSync(iconPath, svg);
    } else {
        // For ICO and ICNS, save as PNG for now (electron-builder can convert)
        const pngPath = iconPath.replace(/\.(ico|icns)$/, '.png');
        fs.writeFileSync(pngPath, svg);
        
        // Try to convert using imagemagick if available
        try {
            await execAsync(`convert "${pngPath}" "${iconPath}"`);
            fs.unlinkSync(pngPath); // Remove PNG if conversion successful
        } catch (error) {
            // If conversion fails, keep the PNG and log warning
            log(`Warning: Could not convert ${iconPath}, using PNG instead`);
            if (iconPath !== pngPath) {
                fs.renameSync(pngPath, iconPath);
            }
        }
    }
}

async function createDMGBackground(bgPath) {
    // Create a simple gradient background
    const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="540" height="380" viewBox="0 0 540 380" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1a1a2e"/>
      <stop offset="100%" stop-color="#16213e"/>
    </linearGradient>
  </defs>
  <rect width="540" height="380" fill="url(#bg)"/>
  <text x="270" y="50" text-anchor="middle" fill="#eee" font-family="Arial, sans-serif" font-size="24" font-weight="bold">Gremlin ShadTail Trader</text>
  <text x="270" y="80" text-anchor="middle" fill="#aaa" font-family="Arial, sans-serif" font-size="14">Drag to Applications folder to install</text>
</svg>`;
    
    fs.writeFileSync(bgPath, svg);
}

async function createEntitlements(entitlementsPath) {
    const entitlements = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.device.camera</key>
    <true/>
    <key>com.apple.security.personal-information.location</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.files.downloads.read-write</key>
    <true/>
</dict>
</plist>`;
    
    fs.writeFileSync(entitlementsPath, entitlements);
}

if (require.main === module) {
    prebuild();
}

module.exports = prebuild;