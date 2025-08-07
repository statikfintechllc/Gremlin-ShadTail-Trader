#!/usr/bin/env python3
"""
Test script to validate backend health check functionality
"""

import asyncio
import requests
import json
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_basic_health():
    """Test basic health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Basic health check: {data['status']}")
            return True
        else:
            print(f"✗ Basic health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Basic health check error: {e}")
        return False

async def test_comprehensive_health():
    """Test comprehensive health endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/system/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Comprehensive health check: {data['system']['status']}")
            print(f"  Health score: {data['system'].get('health_score', 'N/A')}")
            print(f"  Agent imports: {data['summary']['successful_imports']}/{data['summary']['total_agents']}")
            
            # Show any failed imports
            failed_imports = [name for name, status in data['agents']['import_status'].items() 
                            if isinstance(status, str) and status.startswith('failed')]
            if failed_imports:
                print(f"  Failed imports: {failed_imports}")
            
            return data['system']['status'] in ['healthy', 'degraded']
        else:
            print(f"✗ Comprehensive health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Comprehensive health check error: {e}")
        return False

async def test_agent_imports():
    """Test agent imports directly"""
    print("\nTesting agent imports directly...")
    
    # Test imports that should work
    test_imports = [
        ("FastAPI server", "from backend.server import app"),
        ("Main system", "from backend.main import GremlinTradingSystem"),
        ("Agent coordinator", "from backend.Gremlin_Trade_Core.agent_coordinator import AgentCoordinator"),
    ]
    
    for name, import_statement in test_imports:
        try:
            exec(import_statement)
            print(f"✓ {name}: Import successful")
        except Exception as e:
            print(f"✗ {name}: Import failed - {e}")

async def main():
    """Main test function"""
    print("🧪 Testing Backend Health Check Functionality")
    print("=" * 50)
    
    # Test direct imports first
    await test_agent_imports()
    
    print("\n📡 Testing health endpoints...")
    print("Note: Backend server must be running on localhost:8000")
    print("Run: cd backend && python server.py")
    print()
    
    # Test basic health
    basic_ok = await test_basic_health()
    
    # Test comprehensive health
    comprehensive_ok = await test_comprehensive_health()
    
    print("\n📊 Test Results:")
    print(f"Basic health endpoint: {'✓ PASS' if basic_ok else '✗ FAIL'}")
    print(f"Comprehensive health endpoint: {'✓ PASS' if comprehensive_ok else '✗ FAIL'}")
    
    if basic_ok and comprehensive_ok:
        print("\n🎉 All health check tests passed!")
        return 0
    else:
        print("\n❌ Some health check tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)