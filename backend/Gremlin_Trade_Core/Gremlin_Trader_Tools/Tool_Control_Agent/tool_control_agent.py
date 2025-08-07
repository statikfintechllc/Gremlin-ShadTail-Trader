#!/usr/bin/env python3
"""
Gremlin ShadTail Trader - Tool Control Agent
Manages and coordinates all trading tools with memory-based optimization
"""

# Import ALL dependencies through globals.py (required)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from Gremlin_Trade_Core.globals import (
    # Core imports that may be needed
    logging, datetime, asyncio, json, os, sys, Path,
    # Configuration and utilities
    setup_agent_logging, CFG, MEM, LOGS_DIR
)

# Use centralized logging
logger = setup_agent_logging(Path(__file__).stem)


# Import ALL dependencies through globals.py (required)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from Gremlin_Trade_Core.globals import (
    # Core imports
    asyncio, json, logging, datetime, timedelta, timezone, Path,
    Dict, List, Any, Optional, Callable, dataclass, field, Enum,
    subprocess, shlex, importlib, sys,
    # Configuration and logging
    setup_agent_logging, CFG, MEM
)

from Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent.base_memory_agent import BaseMemoryAgent

class ToolStatus(Enum):
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class ToolPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ToolCategory(Enum):
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    STRATEGY = "strategy"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    UTILITY = "utility"

@dataclass
class Tool:
    name: str
    description: str
    category: ToolCategory
    priority: ToolPriority
    status: ToolStatus = ToolStatus.INACTIVE
    module_path: Optional[str] = None
    function_name: Optional[str] = None
    command: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    instance: Any = None
    last_used: Optional[datetime] = None
    use_count: int = 0
    error_count: int = 0
    performance_score: float = 1.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

@dataclass
class ToolExecution:
    tool_name: str
    function: str
    parameters: Dict[str, Any]
    timestamp: datetime
    duration: float
    success: bool
    result: Any = None
    error: Optional[str] = None
    memory_delta: float = 0.0

class ToolControlAgent(BaseMemoryAgent):
    """
    Tool Control Agent manages all trading tools and utilities with memory-based learning
    """
    
    def __init__(self):
        super().__init__("ToolControlAgent", "tool_control")
        
        # Tool registry
        self.tools: Dict[str, Tool] = {}
        self.tool_categories: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        
        # Execution tracking
        self.execution_history: List[ToolExecution] = []
        self.active_executions: Dict[str, ToolExecution] = {}
        self.tool_performance: Dict[str, Dict] = {}
        
        # Resource management
        self.max_concurrent_tools = 5
        self.memory_limit_mb = 500
        self.cpu_limit_percent = 80
        
        # Configuration
        self.auto_initialize_tools = True
        self.tool_timeout_seconds = 300
        self.performance_weight = 0.7
        self.reliability_weight = 0.3
        
        # Initialize built-in tools
        asyncio.create_task(self._register_builtin_tools())
        
        self.logger.info("Tool Control Agent initialized")
    
    async def _register_builtin_tools(self):
        """Register built-in trading tools"""
        try:
            # Data Collection Tools
            await self.register_tool(Tool(
                name="market_data_fetcher",
                description="Fetches real-time and historical market data",
                category=ToolCategory.DATA_COLLECTION,
                priority=ToolPriority.CRITICAL,
                module_path="Gremlin_Trade_Core.market_data_service",
                function_name="get_market_data",
                dependencies=["requests", "pandas"]
            ))
            
            await self.register_tool(Tool(
                name="news_scraper",
                description="Scrapes financial news and sentiment",
                category=ToolCategory.DATA_COLLECTION,
                priority=ToolPriority.HIGH,
                command="python -m tools.news_scraper",
                dependencies=["beautifulsoup4", "requests"]
            ))
            
            # Analysis Tools
            await self.register_tool(Tool(
                name="technical_analyzer",
                description="Performs technical analysis on price data",
                category=ToolCategory.ANALYSIS,
                priority=ToolPriority.HIGH,
                module_path="tools.technical_analysis",
                function_name="analyze_symbol"
            ))
            
            await self.register_tool(Tool(
                name="sentiment_analyzer",
                description="Analyzes market sentiment from news and social media",
                category=ToolCategory.ANALYSIS,
                priority=ToolPriority.MEDIUM,
                module_path="tools.sentiment_analysis",
                function_name="analyze_sentiment"
            ))
            
            await self.register_tool(Tool(
                name="risk_calculator",
                description="Calculates portfolio and position risk metrics",
                category=ToolCategory.ANALYSIS,
                priority=ToolPriority.HIGH,
                module_path="tools.risk_analysis",
                function_name="calculate_risk"
            ))
            
            # Strategy Tools
            await self.register_tool(Tool(
                name="backtester",
                description="Backtests trading strategies",
                category=ToolCategory.STRATEGY,
                priority=ToolPriority.HIGH,
                module_path="tools.backtesting",
                function_name="run_backtest"
            ))
            
            await self.register_tool(Tool(
                name="strategy_optimizer",
                description="Optimizes strategy parameters",
                category=ToolCategory.STRATEGY,
                priority=ToolPriority.MEDIUM,
                module_path="tools.optimization",
                function_name="optimize_strategy"
            ))
            
            # Execution Tools
            await self.register_tool(Tool(
                name="order_manager",
                description="Manages order placement and execution",
                category=ToolCategory.EXECUTION,
                priority=ToolPriority.CRITICAL,
                module_path="tools.order_execution",
                function_name="place_order"
            ))
            
            await self.register_tool(Tool(
                name="position_manager",
                description="Manages portfolio positions",
                category=ToolCategory.EXECUTION,
                priority=ToolPriority.HIGH,
                module_path="tools.position_management",
                function_name="manage_position"
            ))
            
            # Monitoring Tools
            await self.register_tool(Tool(
                name="performance_monitor",
                description="Monitors trading performance",
                category=ToolCategory.MONITORING,
                priority=ToolPriority.HIGH,
                module_path="tools.performance_monitoring",
                function_name="track_performance"
            ))
            
            await self.register_tool(Tool(
                name="alert_system",
                description="Sends trading alerts and notifications",
                category=ToolCategory.MONITORING,
                priority=ToolPriority.MEDIUM,
                module_path="tools.alerts",
                function_name="send_alert"
            ))
            
            # Utility Tools
            await self.register_tool(Tool(
                name="data_cleaner",
                description="Cleans and validates market data",
                category=ToolCategory.UTILITY,
                priority=ToolPriority.LOW,
                module_path="tools.data_cleaning",
                function_name="clean_data"
            ))
            
            await self.register_tool(Tool(
                name="report_generator",
                description="Generates trading reports",
                category=ToolCategory.UTILITY,
                priority=ToolPriority.LOW,
                module_path="tools.reporting",
                function_name="generate_report"
            ))
            
            self.logger.info(f"Registered {len(self.tools)} built-in tools")
            
        except Exception as e:
            self.logger.error(f"Error registering built-in tools: {e}")
    
    async def register_tool(self, tool: Tool) -> bool:
        """Register a new tool"""
        try:
            if tool.name in self.tools:
                self.logger.warning(f"Tool {tool.name} already registered, updating...")
            
            # Validate tool configuration
            if not await self._validate_tool(tool):
                self.logger.error(f"Tool {tool.name} failed validation")
                return False
            
            # Initialize tool performance tracking
            self.tool_performance[tool.name] = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_duration': 0.0,
                'success_rate': 1.0,
                'efficiency_score': 1.0
            }
            
            # Register tool
            self.tools[tool.name] = tool
            self.tool_categories[tool.category].append(tool.name)
            
            # Auto-initialize if enabled
            if self.auto_initialize_tools:
                await self.initialize_tool(tool.name)
            
            # Store in memory
            content = f"Registered tool: {tool.name} ({tool.category.value}, {tool.priority.value} priority)"
            metadata = {
                'tool_name': tool.name,
                'category': tool.category.value,
                'priority': tool.priority.value,
                'dependencies': tool.dependencies
            }
            self.store_memory(content, "tool_registration", metadata)
            
            self.logger.info(f"Successfully registered tool: {tool.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering tool {tool.name}: {e}")
            return False
    
    async def _validate_tool(self, tool: Tool) -> bool:
        """Validate tool configuration"""
        try:
            # Check required fields
            if not tool.name or not tool.description:
                return False
            
            # Check module/command
            if not tool.module_path and not tool.command:
                self.logger.error(f"Tool {tool.name} requires either module_path or command")
                return False
            
            # Validate module path if provided
            if tool.module_path:
                try:
                    # Try to import the module
                    module = importlib.import_module(tool.module_path)
                    if tool.function_name and not hasattr(module, tool.function_name):
                        self.logger.error(f"Function {tool.function_name} not found in {tool.module_path}")
                        return False
                except ImportError as e:
                    self.logger.warning(f"Module {tool.module_path} not available: {e}")
                    # Don't fail validation for missing modules (might be installed later)
            
            # Validate command if provided
            if tool.command:
                try:
                    # Parse command to check syntax
                    shlex.split(tool.command)
                except ValueError as e:
                    self.logger.error(f"Invalid command syntax for {tool.name}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating tool {tool.name}: {e}")
            return False
    
    async def initialize_tool(self, tool_name: str) -> bool:
        """Initialize a tool"""
        try:
            if tool_name not in self.tools:
                self.logger.error(f"Tool {tool_name} not found")
                return False
            
            tool = self.tools[tool_name]
            
            if tool.status == ToolStatus.ACTIVE:
                self.logger.info(f"Tool {tool_name} already active")
                return True
            
            tool.status = ToolStatus.INITIALIZING
            
            # Initialize based on type
            if tool.module_path:
                success = await self._initialize_module_tool(tool)
            elif tool.command:
                success = await self._initialize_command_tool(tool)
            else:
                success = False
            
            if success:
                tool.status = ToolStatus.ACTIVE
                self.logger.info(f"Successfully initialized tool: {tool_name}")
                
                # Store initialization in memory
                content = f"Initialized tool: {tool_name}"
                metadata = {
                    'tool_name': tool_name,
                    'category': tool.category.value,
                    'initialization_time': datetime.now(timezone.utc).isoformat()
                }
                self.store_memory(content, "tool_initialization", metadata)
            else:
                tool.status = ToolStatus.ERROR
                tool.error_count += 1
                self.logger.error(f"Failed to initialize tool: {tool_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error initializing tool {tool_name}: {e}")
            if tool_name in self.tools:
                self.tools[tool_name].status = ToolStatus.ERROR
            return False
    
    async def _initialize_module_tool(self, tool: Tool) -> bool:
        """Initialize a module-based tool"""
        try:
            # Import the module
            module = importlib.import_module(tool.module_path)
            
            if tool.function_name:
                # Get the function
                function = getattr(module, tool.function_name)
                tool.instance = function
            else:
                # Store the module
                tool.instance = module
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing module tool {tool.name}: {e}")
            return False
    
    async def _initialize_command_tool(self, tool: Tool) -> bool:
        """Initialize a command-based tool"""
        try:
            # Test if command is available
            test_command = f"{tool.command} --help"
            process = await asyncio.create_subprocess_shell(
                test_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=5)
            
            # Command is available
            return True
            
        except Exception:
            # Command not available or timeout
            return False
    
    async def execute_tool(self, tool_name: str, function: str = None, **parameters) -> Any:
        """Execute a tool with given parameters"""
        try:
            if tool_name not in self.tools:
                raise ValueError(f"Tool {tool_name} not found")
            
            tool = self.tools[tool_name]
            
            if tool.status != ToolStatus.ACTIVE:
                # Try to initialize if not active
                if not await self.initialize_tool(tool_name):
                    raise RuntimeError(f"Tool {tool_name} is not active and cannot be initialized")
            
            # Check resource limits
            if not await self._check_resource_limits():
                raise RuntimeError("Resource limits exceeded, cannot execute tool")
            
            # Create execution record
            execution = ToolExecution(
                tool_name=tool_name,
                function=function or "default",
                parameters=parameters,
                timestamp=datetime.now(timezone.utc),
                duration=0.0,
                success=False
            )
            
            self.active_executions[f"{tool_name}_{execution.timestamp}"] = execution
            
            # Execute based on tool type
            start_time = datetime.now()
            
            if tool.module_path:
                result = await self._execute_module_tool(tool, function, parameters)
            elif tool.command:
                result = await self._execute_command_tool(tool, parameters)
            else:
                raise ValueError(f"Tool {tool_name} has no execution method")
            
            end_time = datetime.now()
            execution.duration = (end_time - start_time).total_seconds()
            execution.success = True
            execution.result = result
            
            # Update tool usage
            tool.last_used = execution.timestamp
            tool.use_count += 1
            
            # Update performance tracking
            await self._update_tool_performance(tool_name, execution)
            
            # Store execution in memory
            await self._store_tool_execution(execution)
            
            self.logger.info(f"Successfully executed tool {tool_name} in {execution.duration:.2f}s")
            
            return result
            
        except Exception as e:
            execution.success = False
            execution.error = str(e)
            
            # Update error count
            if tool_name in self.tools:
                self.tools[tool_name].error_count += 1
            
            # Update performance tracking
            await self._update_tool_performance(tool_name, execution)
            
            # Store failed execution
            await self._store_tool_execution(execution)
            
            self.logger.error(f"Error executing tool {tool_name}: {e}")
            raise
            
        finally:
            # Remove from active executions
            execution_key = f"{tool_name}_{execution.timestamp}"
            if execution_key in self.active_executions:
                del self.active_executions[execution_key]
            
            # Add to history
            self.execution_history.append(execution)
            
            # Limit history size
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-800:]
    
    async def _execute_module_tool(self, tool: Tool, function: str, parameters: Dict) -> Any:
        """Execute a module-based tool"""
        try:
            if tool.instance is None:
                raise RuntimeError(f"Tool {tool.name} not properly initialized")
            
            if function and hasattr(tool.instance, function):
                # Call specific function
                func = getattr(tool.instance, function)
            elif callable(tool.instance):
                # Instance is the function
                func = tool.instance
            else:
                raise ValueError(f"Tool {tool.name} has no callable function")
            
            # Execute with timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(**parameters),
                    timeout=self.tool_timeout_seconds
                )
            else:
                # Run in executor for sync functions
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: func(**parameters)
                    ),
                    timeout=self.tool_timeout_seconds
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing module tool {tool.name}: {e}")
            raise
    
    async def _execute_command_tool(self, tool: Tool, parameters: Dict) -> Any:
        """Execute a command-based tool"""
        try:
            # Build command with parameters
            command = tool.command
            for key, value in parameters.items():
                command += f" --{key} {shlex.quote(str(value))}"
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.tool_timeout_seconds
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"Command failed with return code {process.returncode}: {stderr.decode()}")
            
            # Try to parse JSON output
            try:
                return json.loads(stdout.decode())
            except json.JSONDecodeError:
                return stdout.decode()
            
        except Exception as e:
            self.logger.error(f"Error executing command tool {tool.name}: {e}")
            raise
    
    async def _check_resource_limits(self) -> bool:
        """Check if resource limits allow tool execution"""
        try:
            # Check concurrent tool limit
            if len(self.active_executions) >= self.max_concurrent_tools:
                return False
            
            # Check memory usage (simplified)
            total_memory = sum(tool.memory_usage for tool in self.tools.values())
            if total_memory > self.memory_limit_mb:
                return False
            
            # Check CPU usage (simplified)
            total_cpu = sum(tool.cpu_usage for tool in self.tools.values())
            if total_cpu > self.cpu_limit_percent:
                return False
            
            return True
            
        except Exception:
            return True  # Allow execution if check fails
    
    async def _update_tool_performance(self, tool_name: str, execution: ToolExecution):
        """Update tool performance metrics"""
        try:
            if tool_name not in self.tool_performance:
                return
            
            perf = self.tool_performance[tool_name]
            
            # Update execution counts
            perf['total_executions'] += 1
            if execution.success:
                perf['successful_executions'] += 1
            else:
                perf['failed_executions'] += 1
            
            # Update success rate
            perf['success_rate'] = perf['successful_executions'] / perf['total_executions']
            
            # Update average duration
            if execution.success:
                total_duration = perf['average_duration'] * (perf['successful_executions'] - 1)
                perf['average_duration'] = (total_duration + execution.duration) / perf['successful_executions']
            
            # Calculate efficiency score
            if perf['average_duration'] > 0:
                perf['efficiency_score'] = min(1.0, 10.0 / perf['average_duration']) * perf['success_rate']
            
            # Update tool performance score
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                tool.performance_score = (
                    self.performance_weight * perf['efficiency_score'] +
                    self.reliability_weight * perf['success_rate']
                )
            
        except Exception as e:
            self.logger.error(f"Error updating performance for {tool_name}: {e}")
    
    async def _store_tool_execution(self, execution: ToolExecution):
        """Store tool execution in memory"""
        try:
            status = "SUCCESS" if execution.success else "FAILURE"
            content = f"Tool execution: {execution.tool_name}.{execution.function} {status} in {execution.duration:.2f}s"
            
            metadata = {
                'tool_name': execution.tool_name,
                'function': execution.function,
                'success': execution.success,
                'duration': execution.duration,
                'parameters': execution.parameters,
                'error': execution.error
            }
            
            self.store_memory(content, "tool_execution", metadata)
            
        except Exception as e:
            self.logger.error(f"Error storing tool execution: {e}")
    
    async def get_tool_recommendations(self, category: ToolCategory = None, 
                                     min_priority: ToolPriority = ToolPriority.LOW) -> List[str]:
        """Get recommended tools based on performance and criteria"""
        try:
            eligible_tools = []
            
            for tool_name, tool in self.tools.items():
                # Check category filter
                if category and tool.category != category:
                    continue
                
                # Check priority filter
                if tool.priority.value < min_priority.value:
                    continue
                
                # Check if tool is functional
                if tool.status in [ToolStatus.ACTIVE, ToolStatus.INACTIVE]:
                    eligible_tools.append((tool_name, tool.performance_score))
            
            # Sort by performance score
            eligible_tools.sort(key=lambda x: x[1], reverse=True)
            
            return [tool_name for tool_name, _ in eligible_tools]
            
        except Exception as e:
            self.logger.error(f"Error getting tool recommendations: {e}")
            return []
    
    async def optimize_tool_usage(self):
        """Optimize tool usage based on historical performance"""
        try:
            self.logger.info("Optimizing tool usage...")
            
            # Analyze performance patterns
            optimization_insights = []
            
            for tool_name, perf in self.tool_performance.items():
                tool = self.tools.get(tool_name)
                if not tool:
                    continue
                
                # Identify underperforming tools
                if perf['success_rate'] < 0.7:
                    optimization_insights.append({
                        'tool': tool_name,
                        'issue': 'low_success_rate',
                        'metric': perf['success_rate'],
                        'action': 'investigate_failures'
                    })
                
                # Identify slow tools
                if perf['average_duration'] > 30:
                    optimization_insights.append({
                        'tool': tool_name,
                        'issue': 'slow_execution',
                        'metric': perf['average_duration'],
                        'action': 'optimize_performance'
                    })
                
                # Identify unused tools
                if tool.use_count == 0 and tool.status == ToolStatus.ACTIVE:
                    optimization_insights.append({
                        'tool': tool_name,
                        'issue': 'unused_tool',
                        'metric': 0,
                        'action': 'consider_deactivation'
                    })
            
            # Store optimization insights
            if optimization_insights:
                content = f"Tool optimization analysis found {len(optimization_insights)} insights"
                metadata = {
                    'insights_count': len(optimization_insights),
                    'insights': optimization_insights
                }
                self.store_memory(content, "tool_optimization", metadata)
            
            self.logger.info(f"Tool optimization completed: {len(optimization_insights)} insights generated")
            
            return optimization_insights
            
        except Exception as e:
            self.logger.error(f"Error optimizing tool usage: {e}")
            return []
    
    async def get_tool_overview(self) -> Dict:
        """Get comprehensive tool overview"""
        try:
            # Count tools by status
            status_counts = {}
            for status in ToolStatus:
                status_counts[status.value] = sum(
                    1 for tool in self.tools.values() if tool.status == status
                )
            
            # Count tools by category
            category_counts = {}
            for category in ToolCategory:
                category_counts[category.value] = len(self.tool_categories[category])
            
            # Get performance summary
            performance_summary = {
                'total_executions': sum(p['total_executions'] for p in self.tool_performance.values()),
                'success_rate': 0.0,
                'average_duration': 0.0
            }
            
            if performance_summary['total_executions'] > 0:
                total_successful = sum(p['successful_executions'] for p in self.tool_performance.values())
                performance_summary['success_rate'] = total_successful / performance_summary['total_executions']
                
                durations = [p['average_duration'] for p in self.tool_performance.values() if p['average_duration'] > 0]
                if durations:
                    performance_summary['average_duration'] = sum(durations) / len(durations)
            
            # Get top performing tools
            top_tools = await self.get_tool_recommendations()
            
            return {
                'agent_status': self.get_agent_state(),
                'total_tools': len(self.tools),
                'status_distribution': status_counts,
                'category_distribution': category_counts,
                'performance_summary': performance_summary,
                'top_performing_tools': top_tools[:5],
                'active_executions': len(self.active_executions),
                'recent_executions': len([e for e in self.execution_history 
                                        if e.timestamp > datetime.now(timezone.utc) - timedelta(hours=1)])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tool overview: {e}")
            return {}
    
    async def process(self):
        """Main tool control processing loop"""
        while self.is_active:
            try:
                # Update status
                active_tools = sum(1 for tool in self.tools.values() if tool.status == ToolStatus.ACTIVE)
                active_executions = len(self.active_executions)
                
                self.update_status(
                    f"Managing {len(self.tools)} tools, "
                    f"{active_tools} active, "
                    f"{active_executions} executing"
                )
                
                # Periodic optimization
                await self.optimize_tool_usage()
                
                # Health check on tools
                for tool_name, tool in self.tools.items():
                    if tool.status == ToolStatus.ACTIVE and tool.error_count > 5:
                        self.logger.warning(f"Tool {tool_name} has high error count: {tool.error_count}")
                        tool.status = ToolStatus.MAINTENANCE
                
                # Clean up old execution history
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                self.execution_history = [
                    e for e in self.execution_history 
                    if e.timestamp > cutoff_time
                ]
                
                # Wait before next cycle
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error in tool control main loop: {e}")
                await asyncio.sleep(300)  # 5 minutes on error

# Example usage
if __name__ == "__main__":
    async def main():
        agent = ToolControlAgent()
        
        try:
            await agent.start()
            
            # Get tool overview
            overview = await agent.get_tool_overview()
            print(f"Tool Control Overview:")
            print(f"  Total Tools: {overview.get('total_tools')}")
            print(f"  Status Distribution: {overview.get('status_distribution')}")
            print(f"  Category Distribution: {overview.get('category_distribution')}")
            print(f"  Performance: {overview.get('performance_summary')}")
            
            # Test tool execution (if available)
            try:
                result = await agent.execute_tool("market_data_fetcher", symbol="AAPL")
                print(f"Tool execution result: {result}")
            except Exception as e:
                print(f"Tool execution test failed: {e}")
            
            # Get tool recommendations
            recommendations = await agent.get_tool_recommendations(ToolCategory.ANALYSIS)
            print(f"Analysis Tool Recommendations: {recommendations}")
            
        finally:
            await agent.stop()
    
    asyncio.run(main())
