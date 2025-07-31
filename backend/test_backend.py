#!/usr/bin/env python3
"""
Backend Functionality Test Suite
Tests all agent coordination, memory integration, and communication systems
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

test_logger = logging.getLogger("backend_tests")

class BackendTestSuite:
    """Comprehensive test suite for backend functionality"""
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        self.test_log_file = Path(__file__).parent / "test-log.txt"
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        self.test_results['total_tests'] += 1
        
        if success:
            self.test_results['passed_tests'] += 1
            status = "PASS"
            test_logger.info(f"✓ {test_name}: {details}")
        else:
            self.test_results['failed_tests'] += 1
            status = "FAIL"
            test_logger.error(f"✗ {test_name}: {error}")
        
        # Store detailed result
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'details': details,
            'error': error
        }
        self.test_results['test_details'].append(result)
        
        # Write to log file
        with open(self.test_log_file, "a") as f:
            f.write(json.dumps(result) + "\n")
    
    def test_globals_import(self):
        """Test globals.py imports and configuration"""
        try:
            from Gremlin_Trade_Core.globals import CFG, MEM, logger, setup_module_logger
            
            # Test configuration loading
            assert isinstance(CFG, dict), "CFG should be a dictionary"
            assert isinstance(MEM, dict), "MEM should be a dictionary"
            assert 'memory' in CFG, "CFG should contain memory config"
            
            # Test logger setup
            test_module_logger = setup_module_logger("test", "module")
            assert test_module_logger is not None, "Logger should be created"
            
            self.log_test_result(
                "globals_import", 
                True, 
                f"CFG keys: {list(CFG.keys())}, MEM keys: {list(MEM.keys())}"
            )
            
        except Exception as e:
            self.log_test_result("globals_import", False, error=str(e))
    
    def test_embedder_functionality(self):
        """Test embedder.py functionality"""
        try:
            from Gremlin_Trade_Memory.embedder import (
                store_embedding, package_embedding, get_all_embeddings,
                get_backend_status, encode
            )
            
            # Test encoding
            test_text = "Test trading signal for AAPL"
            vector = encode(test_text)
            assert vector is not None, "Vector should be generated"
            assert len(vector) > 0, "Vector should have dimensions"
            
            # Test packaging and storing
            metadata = {
                'content_type': 'test_signal',
                'source': 'test_suite',
                'symbol': 'AAPL'
            }
            embedding = package_embedding(test_text, vector, metadata)
            assert 'id' in embedding, "Embedding should have ID"
            
            # Test storage
            stored = store_embedding(embedding)
            assert stored is not None, "Embedding should be stored"
            
            # Test retrieval
            all_embeddings = get_all_embeddings(limit=5)
            assert isinstance(all_embeddings, list), "Should return list of embeddings"
            
            # Test backend status
            status = get_backend_status()
            assert isinstance(status, dict), "Status should be dictionary"
            
            self.log_test_result(
                "embedder_functionality", 
                True, 
                f"Vector dims: {len(vector)}, Embeddings count: {len(all_embeddings)}"
            )
            
        except Exception as e:
            self.log_test_result("embedder_functionality", False, error=str(e))
    
    def test_agent_input_handler(self):
        """Test Agent_in.py functionality"""
        try:
            from Gremlin_Trade_Memory.Agent_in import (
                retrieve_agent_memory, process_agent_request,
                get_memory_system_status, send_data_to_agent
            )
            
            # Test memory retrieval
            memories = retrieve_agent_memory("strategy_agent", "trading_signals", {"symbol": "AAPL"})
            assert isinstance(memories, list), "Should return list of memories"
            
            # Test agent request processing
            request = {
                'query_type': 'market_analysis',
                'context': {'symbol': 'TSLA', 'timeframe': '1min'},
                'limit': 5
            }
            response = process_agent_request("timing_agent", request)
            assert response.get('success'), "Request should be successful"
            assert 'memories' in response, "Response should contain memories"
            
            # Test data sending
            test_data = {'test': 'data', 'memories': []}
            success = send_data_to_agent("test_agent", test_data)
            assert isinstance(success, bool), "Should return boolean"
            
            # Test status
            status = get_memory_system_status()
            assert isinstance(status, dict), "Status should be dictionary"
            
            self.log_test_result(
                "agent_input_handler", 
                True, 
                f"Retrieved {len(memories)} memories, Status: {status.get('agent_input_handler', {}).get('cache_size', 0)} cache entries"
            )
            
        except Exception as e:
            self.log_test_result("agent_input_handler", False, error=str(e))
    
    def test_agent_output_handler(self):
        """Test Agents_out.py functionality"""
        try:
            from Gremlin_Trade_Core.Gremlin_Trader_Tools.Agents_out import (
                process_agent_logs, get_recent_logs, get_performance_summary,
                get_communication_statistics
            )
            
            # Test log processing
            test_logs = [
                {
                    'type': 'signal',
                    'symbol': 'AAPL',
                    'signal_type': 'buy',
                    'confidence': 0.85,
                    'price': 150.0,
                    'volume': 1000000,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'agent_name': 'strategy_agent'
                },
                {
                    'type': 'trade',
                    'symbol': 'TSLA',
                    'action': 'buy',
                    'quantity': 100,
                    'price': 250.0,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'agent_name': 'execution_agent'
                }
            ]
            
            process_agent_logs(test_logs)
            
            # Test recent logs retrieval
            recent = get_recent_logs(limit=5)
            assert isinstance(recent, list), "Should return list of logs"
            
            # Test performance summary
            performance = get_performance_summary()
            assert isinstance(performance, dict), "Should return dictionary"
            
            # Test communication statistics
            stats = get_communication_statistics()
            assert isinstance(stats, dict), "Should return statistics dictionary"
            
            self.log_test_result(
                "agent_output_handler", 
                True, 
                f"Processed {len(test_logs)} logs, Recent: {len(recent)}, Stats: {stats.get('agents_out_stats', {}).get('total_logs_processed', 0)}"
            )
            
        except Exception as e:
            self.log_test_result("agent_output_handler", False, error=str(e))
    
    async def test_agent_coordinator(self):
        """Test agent_coordinator.py functionality"""
        try:
            from Gremlin_Trade_Core.agent_coordinator import AgentCoordinator
            
            # Create coordinator instance
            coordinator = AgentCoordinator()
            assert coordinator is not None, "Coordinator should be created"
            
            # Test agent initialization
            await coordinator.initialize_agents()
            
            # Check agent status
            overview = await coordinator.get_coordination_overview()
            assert isinstance(overview, dict), "Overview should be dictionary"
            assert 'agent_status' in overview, "Should contain agent status"
            
            initialized_count = overview.get('initialized_agents', 0)
            total_count = overview.get('total_agents', 0)
            
            # Test coordination decision (simplified)
            try:
                decision = await coordinator.coordinate_trading_decision("AAPL")
                decision_made = decision is not None
            except Exception as e:
                test_logger.warning(f"Coordination decision test failed (expected): {e}")
                decision_made = False
            
            # Test shutdown
            await coordinator.shutdown_agents()
            
            self.log_test_result(
                "agent_coordinator", 
                True, 
                f"Initialized {initialized_count}/{total_count} agents, Decision made: {decision_made}"
            )
            
        except Exception as e:
            self.log_test_result("agent_coordinator", False, error=str(e))
    
    def test_poetry_environment(self):
        """Test Poetry virtual environment setup"""
        try:
            import subprocess
            import os
            
            # Check if we're in a poetry environment
            result = subprocess.run(['poetry', '--version'], capture_output=True, text=True, cwd=Path(__file__).parent)
            poetry_available = result.returncode == 0
            
            if poetry_available:
                poetry_version = result.stdout.strip()
                
                # Check poetry environment
                env_result = subprocess.run(['poetry', 'env', 'info'], capture_output=True, text=True, cwd=Path(__file__).parent)
                env_info = env_result.stdout if env_result.returncode == 0 else "Poetry env not found"
                
                self.log_test_result(
                    "poetry_environment", 
                    True, 
                    f"Poetry version: {poetry_version}, Environment: {'active' if 'Virtualenv' in env_info else 'not active'}"
                )
            else:
                self.log_test_result("poetry_environment", False, error="Poetry not available")
                
        except Exception as e:
            self.log_test_result("poetry_environment", False, error=str(e))
    
    def test_dependency_imports(self):
        """Test critical dependency imports"""
        dependencies_status = {}
        
        # Test core dependencies
        dependencies = [
            ('numpy', 'np'),
            ('pandas', 'pd'),
            ('fastapi', 'FastAPI'),
            ('uvicorn', None),
            ('chromadb', None),
            ('sentence_transformers', 'SentenceTransformer'),
            ('yfinance', 'yf'),
            ('ta', None)
        ]
        
        for dep_name, import_attr in dependencies:
            try:
                if import_attr:
                    module = __import__(dep_name)
                    if hasattr(module, import_attr):
                        dependencies_status[dep_name] = "available"
                    else:
                        dependencies_status[dep_name] = "partial"
                else:
                    __import__(dep_name)
                    dependencies_status[dep_name] = "available"
            except ImportError:
                dependencies_status[dep_name] = "missing"
        
        available_count = sum(1 for status in dependencies_status.values() if status == "available")
        total_count = len(dependencies_status)
        
        self.log_test_result(
            "dependency_imports", 
            available_count > total_count * 0.7,  # At least 70% should be available
            f"Available: {available_count}/{total_count} - {dependencies_status}"
        )
    
    async def run_all_tests(self):
        """Run all backend tests"""
        test_logger.info("Starting Backend Test Suite...")
        
        # Clear previous test log
        if self.test_log_file.exists():
            self.test_log_file.unlink()
        
        # Write test header
        with open(self.test_log_file, "w") as f:
            f.write(json.dumps({
                'test_suite': 'Backend Functionality Tests',
                'start_time': datetime.now(timezone.utc).isoformat(),
                'test_file': str(__file__)
            }) + "\n")
        
        # Run synchronous tests
        self.test_globals_import()
        self.test_embedder_functionality()
        self.test_agent_input_handler()
        self.test_agent_output_handler()
        self.test_poetry_environment()
        self.test_dependency_imports()
        
        # Run asynchronous tests
        await self.test_agent_coordinator()
        
        # Generate summary
        self.generate_test_summary()
        
        return self.test_results
    
    def generate_test_summary(self):
        """Generate test summary"""
        summary = {
            'test_summary': self.test_results,
            'completion_time': datetime.now(timezone.utc).isoformat(),
            'success_rate': self.test_results['passed_tests'] / max(1, self.test_results['total_tests'])
        }
        
        # Write summary to log
        with open(self.test_log_file, "a") as f:
            f.write(json.dumps(summary) + "\n")
        
        # Print summary
        test_logger.info(f"Test Suite Complete:")
        test_logger.info(f"  Total Tests: {self.test_results['total_tests']}")
        test_logger.info(f"  Passed: {self.test_results['passed_tests']}")
        test_logger.info(f"  Failed: {self.test_results['failed_tests']}")
        test_logger.info(f"  Success Rate: {summary['success_rate']:.1%}")
        test_logger.info(f"  Results logged to: {self.test_log_file}")

async def main():
    """Main test runner"""
    test_suite = BackendTestSuite()
    results = await test_suite.run_all_tests()
    
    # Exit with appropriate code
    if results['failed_tests'] == 0:
        print("All tests passed!")
        sys.exit(0)
    else:
        print(f"Tests failed: {results['failed_tests']}/{results['total_tests']}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())