#!/usr/bin/env python3

"""
Gremlin ShadTail Trader - Base Memory-Enabled Agent
Provides common memory functionality for all trading agents
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import memory system
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from Gremlin_Trade_Memory.embedder import (
        get_chroma_client, encode, init_metadata_database,
        memory_vectors, active_positions, trade_signals, market_data_cache
    )
    from Gremlin_Trade_Core.globals import logger
    MEMORY_AVAILABLE = True
except ImportError as e:
    print(f"Memory system not available: {e}")
    MEMORY_AVAILABLE = False
    logger = None

class BaseMemoryAgent:
    """Base class for all memory-enabled trading agents"""
    
    def __init__(self, agent_name: str, agent_type: str):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(f"agent.{agent_name}")
        
        # Memory system integration
        self.chroma_client = None
        self.collection = None
        self.memory_cache = {}
        self.learning_data = []
        
        # Agent state
        self.is_active = False
        self.last_update = None
        self.performance_metrics = {
            'decisions_made': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'accuracy_rate': 0.0,
            'total_profit_loss': 0.0
        }
        
        # Initialize memory system
        self._init_memory()
    
    def _init_memory(self):
        """Initialize memory system for this agent"""
        if not MEMORY_AVAILABLE:
            self.logger.warning("Memory system not available - operating without persistence")
            return
            
        try:
            self.chroma_client, self.collection = get_chroma_client()
            if self.collection:
                self.logger.info(f"Agent {self.agent_name} connected to memory system")
                # Load existing memories for this agent
                self._load_agent_memories()
            else:
                self.logger.warning("ChromaDB collection not available")
        except Exception as e:
            self.logger.error(f"Failed to initialize memory system: {e}")
    
    def _load_agent_memories(self):
        """Load existing memories specific to this agent"""
        try:
            if not self.collection:
                return
                
            # Query memories for this agent
            results = self.collection.query(
                query_texts=[f"agent:{self.agent_name}"],
                n_results=100,
                where={"agent_type": self.agent_type}
            )
            
            if results['documents']:
                self.logger.info(f"Loaded {len(results['documents'][0])} memories for {self.agent_name}")
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    self.memory_cache[results['ids'][0][i]] = {
                        'content': doc,
                        'metadata': metadata,
                        'timestamp': metadata.get('timestamp', datetime.now().isoformat())
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to load agent memories: {e}")
    
    def store_memory(self, content: str, memory_type: str, metadata: Dict = None):
        """Store a memory in the vector database"""
        if not self.collection:
            self.logger.warning("Cannot store memory - no collection available")
            return None
            
        try:
            memory_id = f"{self.agent_id}_{int(time.time() * 1000)}"
            
            # Prepare metadata
            full_metadata = {
                'agent_name': self.agent_name,
                'agent_type': self.agent_type,
                'agent_id': self.agent_id,
                'memory_type': memory_type,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                **(metadata or {})
            }
            
            # Store in ChromaDB
            self.collection.add(
                documents=[content],
                metadatas=[full_metadata],
                ids=[memory_id]
            )
            
            # Cache locally
            self.memory_cache[memory_id] = {
                'content': content,
                'metadata': full_metadata,
                'timestamp': full_metadata['timestamp']
            }
            
            self.logger.debug(f"Stored memory: {memory_type} - {content[:100]}...")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}")
            return None
    
    def retrieve_memories(self, query: str, memory_type: str = None, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories based on query"""
        if not self.collection:
            return []
            
        try:
            # Build where clause
            where_clause = {"agent_type": self.agent_type}
            if memory_type:
                where_clause["memory_type"] = memory_type
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause
            )
            
            memories = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 1.0
                    
                    memories.append({
                        'id': results['ids'][0][i],
                        'content': doc,
                        'metadata': metadata,
                        'relevance': 1.0 - distance,  # Convert distance to relevance
                        'timestamp': metadata.get('timestamp')
                    })
            
            return memories
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    def learn_from_outcome(self, decision: str, outcome: str, success: bool, profit_loss: float = 0.0):
        """Learn from trading decisions and outcomes"""
        try:
            # Update performance metrics
            self.performance_metrics['decisions_made'] += 1
            if success:
                self.performance_metrics['successful_trades'] += 1
            else:
                self.performance_metrics['failed_trades'] += 1
            
            self.performance_metrics['total_profit_loss'] += profit_loss
            
            # Recalculate accuracy
            total_trades = self.performance_metrics['successful_trades'] + self.performance_metrics['failed_trades']
            if total_trades > 0:
                self.performance_metrics['accuracy_rate'] = self.performance_metrics['successful_trades'] / total_trades
            
            # Store learning experience
            learning_content = f"Decision: {decision}\nOutcome: {outcome}\nSuccess: {success}\nP&L: {profit_loss}"
            
            self.store_memory(
                content=learning_content,
                memory_type="learning_experience",
                metadata={
                    'decision': decision,
                    'outcome': outcome,
                    'success': success,
                    'profit_loss': profit_loss,
                    'accuracy_rate': self.performance_metrics['accuracy_rate']
                }
            )
            
            self.logger.info(f"Learned from outcome - Success: {success}, Accuracy: {self.performance_metrics['accuracy_rate']:.2%}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn from outcome: {e}")
    
    def get_similar_experiences(self, current_situation: str, limit: int = 5) -> List[Dict]:
        """Get similar past experiences to help with current decision"""
        return self.retrieve_memories(
            query=current_situation,
            memory_type="learning_experience",
            limit=limit
        )
    
    def get_agent_state(self) -> Dict:
        """Get current agent state including performance metrics"""
        return {
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'agent_id': self.agent_id,
            'is_active': self.is_active,
            'last_update': self.last_update,
            'performance_metrics': self.performance_metrics,
            'memory_count': len(self.memory_cache),
            'memory_available': MEMORY_AVAILABLE
        }
    
    def update_status(self, status: str, metadata: Dict = None):
        """Update agent status with memory storage"""
        self.last_update = datetime.now(timezone.utc).isoformat()
        
        # Store status update in memory
        self.store_memory(
            content=f"Status update: {status}",
            memory_type="status_update",
            metadata={
                'status': status,
                **(metadata or {})
            }
        )
        
        self.logger.info(f"Agent {self.agent_name} status: {status}")
    
    async def start(self):
        """Start the agent"""
        self.is_active = True
        self.update_status("Agent started")
        self.logger.info(f"Agent {self.agent_name} started")
    
    async def stop(self):
        """Stop the agent"""
        self.is_active = False
        self.update_status("Agent stopped")
        self.logger.info(f"Agent {self.agent_name} stopped")
    
    async def process(self):
        """Main processing loop - to be overridden by specific agents"""
        raise NotImplementedError("Subclasses must implement process method")
