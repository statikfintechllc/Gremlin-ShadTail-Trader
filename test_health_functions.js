// Extract health check functions from main.js for testing
// This simulates the functions in electron/main.js

// Add function to check comprehensive backend health
async function checkBackendHealth(maxAttempts = 3) {
  console.log('Checking comprehensive backend health...');
  
  for (let i = 0; i < maxAttempts; i++) {
    try {
      // Use node-fetch or built-in fetch (Node 18+)
      let fetch;
      try {
        fetch = (await import('node-fetch')).default;
      } catch {
        // Fallback for newer Node.js versions with built-in fetch
        fetch = globalThis.fetch;
      }
      
      // Check comprehensive health endpoint
      const response = await fetch('http://localhost:8000/api/system/health');
      if (response.ok) {
        const healthData = await response.json();
        console.log(`Backend health check ${i + 1}: ${healthData.system.status}`);
        
        if (healthData.system.status === 'healthy') {
          console.log('Backend is fully healthy with all agents operational');
          return { healthy: true, data: healthData };
        } else if (healthData.system.status === 'degraded') {
          console.log('Backend is operational but some agents have issues');
          return { healthy: true, degraded: true, data: healthData };
        } else {
          console.log('Backend is unhealthy:', healthData.system);
          return { healthy: false, data: healthData };
        }
      }
    } catch (error) {
      console.log(`Backend health check ${i + 1} failed:`, error.message);
    }
    
    if (i < maxAttempts - 1) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  return { healthy: false, error: 'Health check failed after retries' };
}

// Add function to wait for backend to be ready
async function waitForBackend(maxAttempts = 30, delayMs = 1000) {
  console.log('Waiting for backend to be ready...');
  
  for (let i = 0; i < maxAttempts; i++) {
    try {
      let fetch;
      try {
        fetch = (await import('node-fetch')).default;
      } catch {
        fetch = globalThis.fetch;
      }
      
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          console.log(`Backend is ready after ${i + 1} attempts`);
          // Now check comprehensive health
          const healthCheck = await checkBackendHealth();
          return healthCheck;
        }
      }
    } catch (error) {
      // Backend not ready yet
    }
    
    console.log(`Backend check ${i + 1}/${maxAttempts}...`);
    await new Promise(resolve => setTimeout(resolve, delayMs));
  }
  
  console.error('Backend failed to start within timeout');
  return { healthy: false, error: 'Backend startup timeout' };
}

module.exports = { checkBackendHealth, waitForBackend };