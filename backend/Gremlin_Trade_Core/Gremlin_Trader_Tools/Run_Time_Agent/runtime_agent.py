#!/usr/bin/env python3
"""
Gremlin ShadTail Trader - Runtime Agent
Advanced runtime orchestration agent with memory-based learning and system coordination
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


import asyncio
import json
import logging
import time
import psutil
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import queue
import weakref

# Import base memory agent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent.base_memory_agent import BaseMemoryAgent

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class AgentState(Enum):
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class Task:
    task_id: str
    name: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    
    def get_duration(self) -> Optional[timedelta]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def get_age(self) -> timedelta:
        return datetime.now(timezone.utc) - self.created_at

@dataclass
class AgentInfo:
    agent_name: str
    agent_type: str
    state: AgentState
    last_heartbeat: datetime
    performance_metrics: Dict[str, Any]
    memory_usage: float
    cpu_usage: float
    error_count: int = 0
    restart_count: int = 0

class RuntimeAgent(BaseMemoryAgent):
    """
    Advanced runtime orchestration agent that manages system resources,
    coordinates other agents, and optimizes performance with memory-based learning
    """
    
    def __init__(self):
        super().__init__("RuntimeAgent", "runtime")
        
        # Task management
        self.task_queue = asyncio.PriorityQueue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        
        # Agent management
        self.managed_agents: Dict[str, AgentInfo] = {}
        self.agent_instances: Dict[str, Any] = {}  # WeakValueDictionary would be better
        
        # System monitoring
        self.system_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_io': 0.0,
            'load_average': 0.0
        }
        
        # Performance optimization
        self.performance_history = []
        self.optimization_rules = {}
        self.auto_scaling_enabled = True
        self.max_concurrent_tasks = 10
        
        # Error handling and recovery
        self.error_patterns = {}
        self.recovery_strategies = {}
        self.circuit_breakers = {}
        
        # Load runtime configuration from memory
        self._load_runtime_config()
        
        # Start system monitoring
        self.monitoring_task = None
        
        self.logger.info("Runtime Agent initialized with memory integration")
    
    def _load_runtime_config(self):
        """Load runtime configuration and patterns from memory"""
        try:
            # Retrieve runtime performance memories
            runtime_memories = self.retrieve_memories(
                query="runtime performance optimization task execution",
                memory_type="runtime_performance",
                limit=50
            )
            
            # Load performance patterns
            for memory in runtime_memories:
                metadata = memory.get('metadata', {})
                
                # Extract optimization patterns
                if 'optimization_type' in metadata:
                    opt_type = metadata['optimization_type']
                    if opt_type not in self.optimization_rules:
                        self.optimization_rules[opt_type] = []
                    
                    self.optimization_rules[opt_type].append({
                        'condition': metadata.get('condition'),
                        'action': metadata.get('action'),
                        'success_rate': metadata.get('success_rate', 0.0),
                        'learned_at': metadata.get('timestamp')
                    })
            
            # Retrieve error pattern memories
            error_memories = self.retrieve_memories(
                query="error pattern failure recovery",
                memory_type="error_pattern",
                limit=30
            )
            
            # Load error patterns and recovery strategies
            for memory in error_memories:
                metadata = memory.get('metadata', {})
                error_type = metadata.get('error_type')
                
                if error_type:
                    if error_type not in self.error_patterns:
                        self.error_patterns[error_type] = {
                            'count': 0,
                            'patterns': [],
                            'recovery_success_rate': 0.0
                        }
                    
                    self.error_patterns[error_type]['count'] += 1
                    self.error_patterns[error_type]['patterns'].append({
                        'context': metadata.get('context'),
                        'recovery_action': metadata.get('recovery_action'),
                        'success': metadata.get('recovery_success', False)
                    })
            
            self.logger.info(f"Loaded runtime configuration from {len(runtime_memories)} memories")
            
        except Exception as e:
            self.logger.error(f"Error loading runtime configuration: {e}")
    
    async def start_monitoring(self):
        """Start system monitoring task"""
        if not self.monitoring_task or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self._monitor_system())
            self.logger.info("System monitoring started")
    
    async def stop_monitoring(self):
        """Stop system monitoring task"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.logger.info("System monitoring stopped")
    
    async def _monitor_system(self):
        """Continuous system monitoring loop"""
        while self.is_active:
            try:
                # Collect system metrics
                self.system_metrics.update({
                    'cpu_usage': psutil.cpu_percent(interval=1),
                    'memory_usage': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
                })
                
                # Monitor network I/O
                try:
                    net_io = psutil.net_io_counters()
                    self.system_metrics['network_io'] = net_io.bytes_sent + net_io.bytes_recv
                except:
                    self.system_metrics['network_io'] = 0.0
                
                # Check for performance issues
                await self._check_performance_issues()
                
                # Update agent heartbeats
                await self._update_agent_heartbeats()
                
                # Store system metrics periodically
                if len(self.performance_history) % 12 == 0:  # Every 12 cycles (1 minute)
                    await self._store_system_metrics()
                
                self.performance_history.append({
                    'timestamp': datetime.now(timezone.utc),
                    'metrics': self.system_metrics.copy()
                })
                
                # Keep only last 1000 entries
                if len(self.performance_history) > 1000:
                    self.performance_history = self.performance_history[-1000:]
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _check_performance_issues(self):
        """Check for performance issues and apply optimizations"""
        try:
            # High CPU usage optimization
            if self.system_metrics['cpu_usage'] > 80:
                await self._handle_high_cpu_usage()
            
            # High memory usage optimization
            if self.system_metrics['memory_usage'] > 85:
                await self._handle_high_memory_usage()
            
            # Task queue optimization
            if self.task_queue.qsize() > self.max_concurrent_tasks * 2:
                await self._optimize_task_queue()
            
            # Check for stuck tasks
            await self._check_stuck_tasks()
            
        except Exception as e:
            self.logger.error(f"Error checking performance issues: {e}")
    
    async def _handle_high_cpu_usage(self):
        """Handle high CPU usage scenarios"""
        try:
            # Reduce concurrent tasks
            if self.max_concurrent_tasks > 2:
                self.max_concurrent_tasks = max(2, self.max_concurrent_tasks - 1)
                self.logger.warning(f"Reduced max concurrent tasks to {self.max_concurrent_tasks} due to high CPU")
            
            # Pause low priority agents if necessary
            low_priority_agents = [
                name for name, info in self.managed_agents.items()
                if info.state == AgentState.ACTIVE and 'low_priority' in name.lower()
            ]
            
            for agent_name in low_priority_agents[:2]:  # Pause up to 2 low priority agents
                await self.pause_agent(agent_name)
                self.logger.info(f"Paused {agent_name} to reduce CPU load")
            
            # Store optimization action
            await self._store_optimization_action("high_cpu", "reduced_concurrency")
            
        except Exception as e:
            self.logger.error(f"Error handling high CPU usage: {e}")
    
    async def _handle_high_memory_usage(self):
        """Handle high memory usage scenarios"""
        try:
            # Clear completed task history
            if len(self.completed_tasks) > 100:
                old_tasks = list(self.completed_tasks.keys())[:-50]
                for task_id in old_tasks:
                    del self.completed_tasks[task_id]
                self.logger.info(f"Cleared {len(old_tasks)} old completed tasks")
            
            # Clear performance history
            if len(self.performance_history) > 500:
                self.performance_history = self.performance_history[-250:]
                self.logger.info("Trimmed performance history to reduce memory usage")
            
            # Request garbage collection from agents
            for agent_name in self.managed_agents:
                if agent_name in self.agent_instances:
                    try:
                        agent = self.agent_instances[agent_name]
                        if hasattr(agent, 'cleanup_memory'):
                            await agent.cleanup_memory()
                    except Exception as e:
                        self.logger.error(f"Error requesting memory cleanup from {agent_name}: {e}")
            
            # Store optimization action
            await self._store_optimization_action("high_memory", "memory_cleanup")
            
        except Exception as e:
            self.logger.error(f"Error handling high memory usage: {e}")
    
    async def _optimize_task_queue(self):
        """Optimize task queue when it gets too large"""
        try:
            # Increase concurrent tasks if resources allow
            if (self.system_metrics['cpu_usage'] < 60 and 
                self.system_metrics['memory_usage'] < 70 and
                self.max_concurrent_tasks < 20):
                
                self.max_concurrent_tasks += 1
                self.logger.info(f"Increased max concurrent tasks to {self.max_concurrent_tasks}")
            
            # Cancel low priority tasks if queue is too large
            if self.task_queue.qsize() > self.max_concurrent_tasks * 3:
                cancelled_count = 0
                temp_tasks = []
                
                # Extract tasks from queue
                while not self.task_queue.empty() and cancelled_count < 5:
                    try:
                        priority, task = self.task_queue.get_nowait()
                        if task.priority == TaskPriority.LOW:
                            task.status = TaskStatus.CANCELLED
                            cancelled_count += 1
                            self.logger.info(f"Cancelled low priority task: {task.name}")
                        else:
                            temp_tasks.append((priority, task))
                    except asyncio.QueueEmpty:
                        break
                
                # Put remaining tasks back
                for priority, task in temp_tasks:
                    await self.task_queue.put((priority, task))
                
                if cancelled_count > 0:
                    await self._store_optimization_action("queue_overflow", f"cancelled_{cancelled_count}_tasks")
            
        except Exception as e:
            self.logger.error(f"Error optimizing task queue: {e}")
    
    async def _check_stuck_tasks(self):
        """Check for tasks that may be stuck"""
        try:
            current_time = datetime.now(timezone.utc)
            stuck_tasks = []
            
            for task_id, task_obj in self.running_tasks.items():
                # Find corresponding Task object
                task_info = None
                for task in [*self.completed_tasks.values(), *self.failed_tasks.values()]:
                    if task.task_id == task_id:
                        task_info = task
                        break
                
                if task_info and task_info.started_at:
                    runtime = current_time - task_info.started_at
                    
                    # Consider task stuck if running for more than 10 minutes without timeout
                    if runtime > timedelta(minutes=10) and not task_info.timeout:
                        stuck_tasks.append((task_id, task_info, task_obj))
                    
                    # Or if it exceeded its timeout
                    elif task_info.timeout and runtime.total_seconds() > task_info.timeout:
                        stuck_tasks.append((task_id, task_info, task_obj))
            
            # Handle stuck tasks
            for task_id, task_info, task_obj in stuck_tasks:
                self.logger.warning(f"Detected stuck task: {task_info.name} (running for {runtime})")
                
                # Cancel the task
                task_obj.cancel()
                task_info.status = TaskStatus.FAILED
                task_info.error = "Task timeout/stuck"
                task_info.completed_at = current_time
                
                # Move to failed tasks
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
                self.failed_tasks[task_id] = task_info
                
                # Store error pattern
                await self._store_error_pattern("task_timeout", task_info.name, "task_cancellation")
            
        except Exception as e:
            self.logger.error(f"Error checking stuck tasks: {e}")
    
    async def _update_agent_heartbeats(self):
        """Update agent heartbeat information"""
        try:
            current_time = datetime.now(timezone.utc)
            
            for agent_name, agent_info in self.managed_agents.items():
                if agent_name in self.agent_instances:
                    try:
                        agent = self.agent_instances[agent_name]
                        
                        # Update agent state
                        if hasattr(agent, 'is_active'):
                            agent_info.state = AgentState.ACTIVE if agent.is_active else AgentState.INACTIVE
                        
                        # Update performance metrics
                        if hasattr(agent, 'get_agent_state'):
                            state = agent.get_agent_state()
                            agent_info.performance_metrics = state.get('performance_metrics', {})
                        
                        # Update resource usage (estimated)
                        agent_info.memory_usage = psutil.Process().memory_percent() / len(self.managed_agents)
                        agent_info.cpu_usage = self.system_metrics['cpu_usage'] / len(self.managed_agents)
                        
                        agent_info.last_heartbeat = current_time
                        
                    except Exception as e:
                        agent_info.error_count += 1
                        self.logger.error(f"Error updating heartbeat for {agent_name}: {e}")
                        
                        if agent_info.error_count > 5:
                            agent_info.state = AgentState.ERROR
            
        except Exception as e:
            self.logger.error(f"Error updating agent heartbeats: {e}")
    
    async def _store_system_metrics(self):
        """Store system metrics in memory"""
        try:
            content = f"System metrics: CPU {self.system_metrics['cpu_usage']:.1f}%, Memory {self.system_metrics['memory_usage']:.1f}%, Load {self.system_metrics['load_average']:.2f}"
            
            metadata = {
                'cpu_usage': self.system_metrics['cpu_usage'],
                'memory_usage': self.system_metrics['memory_usage'],
                'disk_usage': self.system_metrics['disk_usage'],
                'network_io': self.system_metrics['network_io'],
                'load_average': self.system_metrics['load_average'],
                'active_tasks': len(self.running_tasks),
                'queue_size': self.task_queue.qsize(),
                'managed_agents': len(self.managed_agents)
            }
            
            self.store_memory(content, "system_metrics", metadata)
            
        except Exception as e:
            self.logger.error(f"Error storing system metrics: {e}")
    
    async def _store_optimization_action(self, issue_type: str, action: str):
        """Store optimization action in memory"""
        try:
            content = f"Runtime optimization: {action} applied for {issue_type}"
            
            metadata = {
                'optimization_type': issue_type,
                'action': action,
                'system_state': self.system_metrics.copy(),
                'success': True  # Will be updated if we track outcomes
            }
            
            self.store_memory(content, "runtime_optimization", metadata)
            
        except Exception as e:
            self.logger.error(f"Error storing optimization action: {e}")
    
    async def _store_error_pattern(self, error_type: str, context: str, recovery_action: str):
        """Store error pattern in memory"""
        try:
            content = f"Error pattern: {error_type} in {context}, recovered with {recovery_action}"
            
            metadata = {
                'error_type': error_type,
                'context': context,
                'recovery_action': recovery_action,
                'system_state': self.system_metrics.copy()
            }
            
            self.store_memory(content, "error_pattern", metadata)
            
        except Exception as e:
            self.logger.error(f"Error storing error pattern: {e}")
    
    async def submit_task(self, name: str, function: Callable, *args, 
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: Optional[float] = None,
                         dependencies: List[str] = None,
                         **kwargs) -> str:
        """Submit a task for execution"""
        try:
            task_id = f"task_{int(time.time() * 1000)}_{len(self.running_tasks)}"
            
            task = Task(
                task_id=task_id,
                name=name,
                function=function,
                args=args,
                kwargs=kwargs,
                priority=priority,
                timeout=timeout,
                dependencies=dependencies or []
            )
            
            # Check dependencies
            if task.dependencies:
                unmet_deps = [dep for dep in task.dependencies 
                             if dep not in self.completed_tasks]
                if unmet_deps:
                    task.status = TaskStatus.PENDING
                    self.logger.info(f"Task {name} waiting for dependencies: {unmet_deps}")
            
            # Add to queue with priority
            await self.task_queue.put((priority.value, task))
            
            self.logger.info(f"Submitted task: {name} (ID: {task_id})")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Error submitting task {name}: {e}")
            raise
    
    async def execute_tasks(self):
        """Execute tasks from the queue"""
        while self.is_active:
            try:
                # Limit concurrent tasks
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(1)
                    continue
                
                try:
                    # Get next task with timeout
                    priority, task = await asyncio.wait_for(
                        self.task_queue.get(), 
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check dependencies again
                if task.dependencies:
                    unmet_deps = [dep for dep in task.dependencies 
                                 if dep not in self.completed_tasks]
                    if unmet_deps:
                        # Put back in queue
                        await self.task_queue.put((priority, task))
                        await asyncio.sleep(1)
                        continue
                
                # Execute task
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now(timezone.utc)
                
                async_task = asyncio.create_task(self._execute_single_task(task))
                self.running_tasks[task.task_id] = async_task
                
                self.logger.info(f"Started executing task: {task.name}")
                
            except Exception as e:
                self.logger.error(f"Error in task execution loop: {e}")
                await asyncio.sleep(1)
    
    async def _execute_single_task(self, task: Task):
        """Execute a single task"""
        try:
            # Apply timeout if specified
            if task.timeout:
                result = await asyncio.wait_for(
                    self._run_task_function(task),
                    timeout=task.timeout
                )
            else:
                result = await self._run_task_function(task)
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now(timezone.utc)
            
            # Move to completed tasks
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
            self.completed_tasks[task.task_id] = task
            
            # Store task performance
            duration = task.get_duration()
            if duration:
                await self._store_task_performance(task, True, duration.total_seconds())
            
            self.logger.info(f"Task completed: {task.name} in {duration}")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = "Task timeout"
            task.completed_at = datetime.now(timezone.utc)
            await self._handle_task_failure(task, "timeout")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now(timezone.utc)
            await self._handle_task_failure(task, "exception")
            
        finally:
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
    
    async def _run_task_function(self, task: Task):
        """Run the actual task function"""
        try:
            if asyncio.iscoroutinefunction(task.function):
                return await task.function(*task.args, **task.kwargs)
            else:
                # Run synchronous function in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, 
                    lambda: task.function(*task.args, **task.kwargs)
                )
        except Exception as e:
            self.logger.error(f"Error running task function {task.name}: {e}")
            raise
    
    async def _handle_task_failure(self, task: Task, failure_type: str):
        """Handle task failure with retry logic"""
        try:
            self.logger.error(f"Task failed: {task.name} - {task.error}")
            
            # Retry logic
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.error = None
                
                # Add back to queue with reduced priority
                retry_priority = max(1, task.priority.value - 1)
                await self.task_queue.put((retry_priority, task))
                
                self.logger.info(f"Retrying task: {task.name} (attempt {task.retries + 1})")
            else:
                # Move to failed tasks
                self.failed_tasks[task.task_id] = task
                
                # Store failure pattern
                await self._store_error_pattern(failure_type, task.name, "task_retry_exhausted")
                
                # Store task performance
                duration = task.get_duration()
                if duration:
                    await self._store_task_performance(task, False, duration.total_seconds())
            
        except Exception as e:
            self.logger.error(f"Error handling task failure: {e}")
    
    async def _store_task_performance(self, task: Task, success: bool, duration: float):
        """Store task performance metrics"""
        try:
            content = f"Task performance: {task.name} {'succeeded' if success else 'failed'} in {duration:.2f}s"
            
            metadata = {
                'task_name': task.name,
                'task_id': task.task_id,
                'success': success,
                'duration': duration,
                'priority': task.priority.value,
                'retries': task.retries,
                'system_state': self.system_metrics.copy()
            }
            
            self.store_memory(content, "task_performance", metadata)
            
        except Exception as e:
            self.logger.error(f"Error storing task performance: {e}")
    
    async def register_agent(self, agent_name: str, agent_instance: Any):
        """Register an agent for monitoring and management"""
        try:
            agent_info = AgentInfo(
                agent_name=agent_name,
                agent_type=getattr(agent_instance, 'agent_type', 'unknown'),
                state=AgentState.INACTIVE,
                last_heartbeat=datetime.now(timezone.utc),
                performance_metrics={},
                memory_usage=0.0,
                cpu_usage=0.0
            )
            
            self.managed_agents[agent_name] = agent_info
            self.agent_instances[agent_name] = agent_instance
            
            self.logger.info(f"Registered agent: {agent_name}")
            
        except Exception as e:
            self.logger.error(f"Error registering agent {agent_name}: {e}")
    
    async def start_agent(self, agent_name: str):
        """Start a managed agent"""
        try:
            if agent_name not in self.agent_instances:
                self.logger.error(f"Agent {agent_name} not registered")
                return False
            
            agent = self.agent_instances[agent_name]
            agent_info = self.managed_agents[agent_name]
            
            agent_info.state = AgentState.STARTING
            
            if hasattr(agent, 'start'):
                if asyncio.iscoroutinefunction(agent.start):
                    await agent.start()
                else:
                    agent.start()
            
            agent_info.state = AgentState.ACTIVE
            agent_info.last_heartbeat = datetime.now(timezone.utc)
            
            self.logger.info(f"Started agent: {agent_name}")
            return True
            
        except Exception as e:
            if agent_name in self.managed_agents:
                self.managed_agents[agent_name].state = AgentState.ERROR
                self.managed_agents[agent_name].error_count += 1
            
            self.logger.error(f"Error starting agent {agent_name}: {e}")
            return False
    
    async def stop_agent(self, agent_name: str):
        """Stop a managed agent"""
        try:
            if agent_name not in self.agent_instances:
                self.logger.error(f"Agent {agent_name} not registered")
                return False
            
            agent = self.agent_instances[agent_name]
            agent_info = self.managed_agents[agent_name]
            
            agent_info.state = AgentState.STOPPING
            
            if hasattr(agent, 'stop'):
                if asyncio.iscoroutinefunction(agent.stop):
                    await agent.stop()
                else:
                    agent.stop()
            
            agent_info.state = AgentState.INACTIVE
            
            self.logger.info(f"Stopped agent: {agent_name}")
            return True
            
        except Exception as e:
            if agent_name in self.managed_agents:
                self.managed_agents[agent_name].state = AgentState.ERROR
                self.managed_agents[agent_name].error_count += 1
            
            self.logger.error(f"Error stopping agent {agent_name}: {e}")
            return False
    
    async def pause_agent(self, agent_name: str):
        """Pause a managed agent"""
        try:
            if agent_name not in self.agent_instances:
                return False
            
            agent_info = self.managed_agents[agent_name]
            
            if agent_info.state == AgentState.ACTIVE:
                agent_info.state = AgentState.PAUSING
                
                # Custom pause logic could go here
                agent_info.state = AgentState.PAUSED
                
                self.logger.info(f"Paused agent: {agent_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error pausing agent {agent_name}: {e}")
            return False
    
    async def get_runtime_overview(self) -> Dict:
        """Get comprehensive runtime overview"""
        try:
            return {
                'agent_status': self.get_agent_state(),
                'system_metrics': self.system_metrics,
                'task_statistics': {
                    'running_tasks': len(self.running_tasks),
                    'queued_tasks': self.task_queue.qsize(),
                    'completed_tasks': len(self.completed_tasks),
                    'failed_tasks': len(self.failed_tasks),
                    'max_concurrent': self.max_concurrent_tasks
                },
                'managed_agents': {
                    name: {
                        'state': info.state.value,
                        'last_heartbeat': info.last_heartbeat.isoformat(),
                        'error_count': info.error_count,
                        'memory_usage': info.memory_usage,
                        'cpu_usage': info.cpu_usage
                    }
                    for name, info in self.managed_agents.items()
                },
                'performance_optimization': {
                    'auto_scaling_enabled': self.auto_scaling_enabled,
                    'optimization_rules': len(self.optimization_rules),
                    'error_patterns': len(self.error_patterns)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting runtime overview: {e}")
            return {}
    
    async def process(self):
        """Main runtime agent processing loop"""
        # Start monitoring and task execution
        await self.start_monitoring()
        
        # Start task execution loop
        task_executor = asyncio.create_task(self.execute_tasks())
        
        try:
            while self.is_active:
                try:
                    # Update status
                    active_agents = len([a for a in self.managed_agents.values() 
                                       if a.state == AgentState.ACTIVE])
                    
                    self.update_status(
                        f"Managing {active_agents} agents, "
                        f"{len(self.running_tasks)} running tasks, "
                        f"CPU: {self.system_metrics['cpu_usage']:.1f}%"
                    )
                    
                    # Periodic health check
                    if len(self.performance_history) % 60 == 0:  # Every 5 minutes
                        await self._perform_health_check()
                    
                    await asyncio.sleep(30)  # Main loop delay
                    
                except Exception as e:
                    self.logger.error(f"Error in runtime agent main loop: {e}")
                    await asyncio.sleep(60)
        
        finally:
            # Cleanup
            task_executor.cancel()
            await self.stop_monitoring()
    
    async def _perform_health_check(self):
        """Perform periodic health check"""
        try:
            unhealthy_agents = []
            
            for name, info in self.managed_agents.items():
                # Check for unresponsive agents
                last_heartbeat = info.last_heartbeat
                if datetime.now(timezone.utc) - last_heartbeat > timedelta(minutes=5):
                    unhealthy_agents.append(name)
                
                # Check for error-prone agents
                if info.error_count > 10:
                    unhealthy_agents.append(name)
            
            if unhealthy_agents:
                self.logger.warning(f"Unhealthy agents detected: {unhealthy_agents}")
                
                # Store health check results
                content = f"Health check: {len(unhealthy_agents)} unhealthy agents detected"
                
                metadata = {
                    'unhealthy_agents': unhealthy_agents,
                    'total_agents': len(self.managed_agents),
                    'system_health_score': (len(self.managed_agents) - len(unhealthy_agents)) / len(self.managed_agents)
                }
                
                self.store_memory(content, "health_check", metadata)
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")

# Example usage
if __name__ == "__main__":
    async def example_task(name: str, delay: int = 1):
        """Example task function"""
        await asyncio.sleep(delay)
        return f"Task {name} completed after {delay}s"
    
    async def main():
        runtime = RuntimeAgent()
        await runtime.start()
        
        # Submit some example tasks
        task1_id = await runtime.submit_task("example_task_1", example_task, "Task1", 2)
        task2_id = await runtime.submit_task("example_task_2", example_task, "Task2", 1, priority=TaskPriority.HIGH)
        
        # Let tasks run
        await asyncio.sleep(5)
        
        # Get overview
        overview = await runtime.get_runtime_overview()
        print(f"Runtime Overview:")
        print(f"  Running Tasks: {overview['task_statistics']['running_tasks']}")
        print(f"  Completed Tasks: {overview['task_statistics']['completed_tasks']}")
        print(f"  CPU Usage: {overview['system_metrics']['cpu_usage']:.1f}%")
        print(f"  Memory Usage: {overview['system_metrics']['memory_usage']:.1f}%")
        
        await runtime.stop()
    
    asyncio.run(main())
