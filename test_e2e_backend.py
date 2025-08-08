#!/usr/bin/env python3
"""
End-to-end test to validate backend restart and health check functionality
"""

import asyncio
import requests
import json
import sys
import time
import subprocess
import signal
import os
from pathlib import Path

class BackendE2ETest:
    def __init__(self):
        self.backend_process = None
        self.test_results = {}
        
    async def start_backend(self):
        """Start the backend server"""
        print("🚀 Starting backend server...")
        
        backend_dir = Path(__file__).parent / "backend"
        cmd = [sys.executable, "server.py"]
        
        self.backend_process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Wait for server to start
        await asyncio.sleep(3)
        print(f"Backend started with PID: {self.backend_process.pid}")
        
    def stop_backend(self):
        """Stop the backend server"""
        if self.backend_process:
            print("🛑 Stopping backend server...")
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                self.backend_process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                # Force kill if needed
                try:
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            self.backend_process = None
            print("Backend stopped")
    
    async def test_basic_health(self):
        """Test basic health endpoint"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            success = response.status_code == 200 and response.json().get("status") == "healthy"
            self.test_results["basic_health"] = success
            print(f"✓ Basic health check: {'PASS' if success else 'FAIL'}")
            return success
        except Exception as e:
            print(f"✗ Basic health check error: {e}")
            self.test_results["basic_health"] = False
            return False
    
    async def test_comprehensive_health(self):
        """Test comprehensive health endpoint"""
        try:
            response = requests.get("http://localhost:8000/api/system/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data['system']['status']
                health_score = data['system'].get('health_score', 0)
                agents_ok = data['summary']['successful_imports']
                total_agents = data['summary']['total_agents']
                
                # Consider degraded as acceptable for testing
                success = status in ['healthy', 'degraded'] and health_score >= 50
                self.test_results["comprehensive_health"] = {
                    "success": success,
                    "status": status,
                    "health_score": health_score,
                    "agents": f"{agents_ok}/{total_agents}"
                }
                
                print(f"✓ Comprehensive health: {'PASS' if success else 'FAIL'}")
                print(f"  Status: {status}, Score: {health_score}, Agents: {agents_ok}/{total_agents}")
                return success
            else:
                print(f"✗ Comprehensive health failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Comprehensive health error: {e}")
            self.test_results["comprehensive_health"] = {"success": False, "error": str(e)}
            return False
    
    async def test_backend_restart(self):
        """Test backend restart scenario"""
        print("\n🔄 Testing backend restart scenario...")
        
        # 1. Verify backend is running
        basic_ok = await self.test_basic_health()
        if not basic_ok:
            print("✗ Backend not running before restart test")
            return False
        
        # 2. Stop backend
        self.stop_backend()
        
        # 3. Verify backend is stopped
        await asyncio.sleep(2)
        try:
            requests.get("http://localhost:8000/health", timeout=2)
            print("✗ Backend still responding after stop")
            return False
        except:
            print("✓ Backend properly stopped")
        
        # 4. Restart backend
        await self.start_backend()
        
        # 5. Wait for backend to be ready
        for i in range(30):  # 30 second timeout
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print(f"✓ Backend restarted successfully after {i+1} seconds")
                    break
            except:
                pass
            await asyncio.sleep(1)
        else:
            print("✗ Backend failed to restart within 30 seconds")
            return False
        
        # 6. Verify health after restart
        health_ok = await self.test_comprehensive_health()
        
        self.test_results["backend_restart"] = health_ok
        return health_ok
    
    async def test_error_handling(self):
        """Test error handling when backend is not available"""
        print("\n🚫 Testing error handling...")
        
        # Stop backend
        self.stop_backend()
        await asyncio.sleep(2)
        
        # Test error responses
        try:
            requests.get("http://localhost:8000/health", timeout=2)
            print("✗ Expected connection error but got response")
            return False
        except requests.exceptions.ConnectionError:
            print("✓ Proper connection error when backend down")
            self.test_results["error_handling"] = True
            return True
        except Exception as e:
            print(f"✗ Unexpected error type: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Backend E2E Test Suite")
        print("=" * 50)
        
        try:
            # Start backend
            await self.start_backend()
            
            # Test 1: Basic health
            print("\n1. Testing basic health endpoint...")
            await self.test_basic_health()
            
            # Test 2: Comprehensive health
            print("\n2. Testing comprehensive health endpoint...")
            await self.test_comprehensive_health()
            
            # Test 3: Backend restart
            await self.test_backend_restart()
            
            # Test 4: Error handling
            await self.test_error_handling()
            
            # Summary
            print("\n📊 Test Results Summary:")
            print("=" * 30)
            
            total_tests = 0
            passed_tests = 0
            
            for test_name, result in self.test_results.items():
                if isinstance(result, dict):
                    success = result.get("success", False)
                else:
                    success = result
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{test_name}: {status}")
                total_tests += 1
                if success:
                    passed_tests += 1
            
            print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                print("🎉 All tests passed! Backend health check system working correctly.")
                return 0
            else:
                print("⚠️  Some tests failed. Check implementation.")
                return 1
                
        finally:
            # Always clean up
            self.stop_backend()

async def main():
    """Main test function"""
    test_suite = BackendE2ETest()
    return await test_suite.run_all_tests()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)