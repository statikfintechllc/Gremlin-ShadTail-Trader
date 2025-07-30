#!/usr/bin/env node

// Prebuild script for Electron Builder
// This script runs before packaging the application

const fs = require('fs');
const path = require('path');

console.log('🔧 Running prebuild script...');

// Ensure required directories exist
const requiredDirs = [
  'dist-electron',
  'frontend/dist',
  'backend'
];

requiredDirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`✓ Created directory: ${dir}`);
  }
});

// Copy backend files to packaged app if needed
const backendSrc = path.join(__dirname, '..', 'backend');
const backendDest = path.join(__dirname, '..', 'dist-electron', 'backend');

if (fs.existsSync(backendSrc) && !fs.existsSync(backendDest)) {
  console.log('✓ Backend directory exists, ready for packaging');
}

console.log('✅ Prebuild completed successfully');
