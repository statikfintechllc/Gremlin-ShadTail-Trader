// Test script to validate Electron backend health check logic
const { checkBackendHealth, waitForBackend } = require('./test_health_functions.js');

async function testHealthCheck() {
    console.log('🧪 Testing Electron Health Check Logic');
    console.log('=====================================');
    
    try {
        console.log('\n1. Testing checkBackendHealth()...');
        const healthResult = await checkBackendHealth();
        console.log('Health check result:', healthResult);
        
        console.log('\n2. Testing waitForBackend()...');
        const backendResult = await waitForBackend(5, 1000); // 5 attempts, 1 second apart
        console.log('Backend wait result:', backendResult);
        
        if (healthResult.healthy) {
            console.log('\n✅ Backend health check logic working correctly!');
            console.log(`Status: ${healthResult.data?.system?.status}`);
            console.log(`Agents: ${healthResult.data?.summary?.successful_imports}/${healthResult.data?.summary?.total_agents}`);
            
            if (healthResult.degraded) {
                console.log('⚠️  Backend is operational but has degraded components');
            }
        } else {
            console.log('\n❌ Backend health check detected issues');
            console.log('Error:', healthResult.error);
        }
        
    } catch (error) {
        console.error('Test failed:', error);
    }
}

testHealthCheck();