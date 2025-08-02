#!/usr/bin/env python3
"""
Agent Input Handler - Receives data from embedder and memory system
and distributes it to agents for decision-making. Central communication hub
for memory retrieval and agent coordination.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Gremlin_Trade_Core.globals import (
    logger, setup_module_logger, CFG, MEM,
    LOGS_DIR, METADATA_DB_PATH, embed_text
)

# Import memory system
from Gremlin_Trade_Memory.embedder import (
    query_embeddings, get_all_embeddings, get_backend_status,
    store_embedding, package_embedding
)

# Setup module logger
agent_in_logger = setup_module_logger("memory", "agent_input_handler")

class AgentInputHandler:
    """Handles all agent inputs from memory system and routes to appropriate agents"""
    
    def __init__(self):
        self.memory_cache = {}
        self.recent_queries = []
        self.retrieval_stats = {
            'total_queries': 0,
            'successful_retrievals': 0,
            'cache_hits': 0,
            'failed_retrievals': 0
        }
        
        # Initialize logging
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        agent_in_logger.info("Agent Input Handler initialized")
    
    def retrieve_agent_memory(self, agent_name: str, query_type: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a specific agent and query type"""
        try:
            self.retrieval_stats['total_queries'] += 1
            
            # Create cache key
            cache_key = f"{agent_name}_{query_type}_{hash(str(context))}"
            
            # Check cache first
            if cache_key in self.memory_cache:
                self.retrieval_stats['cache_hits'] += 1
                agent_in_logger.debug(f"Cache hit for {agent_name} query: {query_type}")
                return self.memory_cache[cache_key]
            
            # Build query based on agent and type
            query_text = self._build_query_text(agent_name, query_type, context)
            
            # Retrieve from embeddings
            memories = query_embeddings(query_text, limit=10)
            
            # Filter memories by relevance to agent
            relevant_memories = self._filter_memories_for_agent(memories, agent_name, query_type)
            
            # Cache the result
            self.memory_cache[cache_key] = relevant_memories
            
            # Clean cache if it gets too large
            if len(self.memory_cache) > 100:
                self._clean_memory_cache()
            
            self.retrieval_stats['successful_retrievals'] += 1
            agent_in_logger.info(f"Retrieved {len(relevant_memories)} memories for {agent_name} - {query_type}")
            
            # Store retrieval event
            self._log_retrieval_event(agent_name, query_type, len(relevant_memories), context)
            
            return relevant_memories
            
        except Exception as e:
            self.retrieval_stats['failed_retrievals'] += 1
            agent_in_logger.error(f"Error retrieving memory for {agent_name}: {e}")
            return []
    
    def _build_query_text(self, agent_name: str, query_type: str, context: Dict[str, Any] = None) -> str:
        """Build appropriate query text based on agent and query type"""
        try:
            base_query = f"{agent_name} {query_type}"
            
            if context:
                if 'symbol' in context:
                    base_query += f" {context['symbol']}"
                if 'signal_type' in context:
                    base_query += f" {context['signal_type']}"
                if 'timeframe' in context:
                    base_query += f" {context['timeframe']}"
                if 'strategy' in context:
                    base_query += f" {context['strategy']}"
                if 'market_condition' in context:
                    base_query += f" {context['market_condition']}"
            
            # Add query type specific terms
            if query_type == "trading_signals":
                base_query += " signal trade decision confidence"
            elif query_type == "market_analysis":
                base_query += " market analysis trend pattern"
            elif query_type == "risk_assessment":
                base_query += " risk management position sizing"
            elif query_type == "strategy_performance":
                base_query += " strategy performance outcome success"
            elif query_type == "coordination_decisions":
                base_query += " coordination decision consensus"
            
            return base_query
            
        except Exception as e:
            agent_in_logger.error(f"Error building query text: {e}")
            return f"{agent_name} {query_type}"
    
    def _filter_memories_for_agent(self, memories: List[Dict[str, Any]], agent_name: str, query_type: str) -> List[Dict[str, Any]]:
        """Filter memories based on relevance to specific agent and query type"""
        try:
            relevant_memories = []
            
            for memory in memories:
                metadata = memory.get('metadata', {})
                
                # Check if memory is relevant to this agent
                is_relevant = False
                
                # Check source relevance
                source = metadata.get('source', '')
                if agent_name.lower() in source.lower():
                    is_relevant = True
                
                # Check content type relevance
                content_type = metadata.get('content_type', '')
                if query_type in content_type or content_type in query_type:
                    is_relevant = True
                
                # Check for general trading relevance
                if query_type in ['trading_signals', 'market_analysis'] and content_type in ['trading_signal', 'market_analysis', 'coordination_decision']:
                    is_relevant = True
                
                # Check importance score
                importance = metadata.get('importance_score', 0.5)
                if importance > 0.7:  # High importance memories are always relevant
                    is_relevant = True
                
                if is_relevant:
                    relevant_memories.append(memory)
            
            # Sort by importance and recency
            relevant_memories.sort(key=lambda x: (
                x.get('metadata', {}).get('importance_score', 0.5),
                x.get('metadata', {}).get('created_at', '')
            ), reverse=True)
            
            return relevant_memories[:10]  # Return top 10 most relevant
            
        except Exception as e:
            agent_in_logger.error(f"Error filtering memories: {e}")
            return memories[:5]  # Return first 5 as fallback
    
    def _clean_memory_cache(self):
        """Clean old entries from memory cache"""
        try:
            # Keep only the 50 most recent cache entries
            if len(self.memory_cache) > 50:
                # This is a simple cleanup - in production might want more sophisticated LRU
                cache_items = list(self.memory_cache.items())
                self.memory_cache = dict(cache_items[-50:])
                agent_in_logger.debug("Cleaned memory cache")
        except Exception as e:
            agent_in_logger.error(f"Error cleaning memory cache: {e}")
    
    def _log_retrieval_event(self, agent_name: str, query_type: str, result_count: int, context: Dict[str, Any] = None):
        """Log memory retrieval event"""
        try:
            event = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': 'memory_retrieval',
                'agent_name': agent_name,
                'query_type': query_type,
                'result_count': result_count,
                'context': context or {},
                'retrieval_stats': self.retrieval_stats.copy()
            }
            
            # Add to recent queries for analysis
            self.recent_queries.append(event)
            
            # Keep only last 100 queries
            if len(self.recent_queries) > 100:
                self.recent_queries = self.recent_queries[-100:]
            
            # Log to file for Agents_out processing
            log_file = LOGS_DIR / "Agent_Retrieval.log"
            with open(log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
            
        except Exception as e:
            agent_in_logger.error(f"Error logging retrieval event: {e}")
    
    def send_data_to_agent(self, agent_name: str, data: Dict[str, Any]) -> bool:
        """Send retrieved data to specific agent (simulation for now)"""
        try:
            # In a full implementation, this would interface with actual agent APIs
            # For now, we log the data transfer and store in memory
            
            transfer_event = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': 'agent_data_transfer',
                'target_agent': agent_name,
                'data_summary': {
                    'memory_count': len(data.get('memories', [])),
                    'context_provided': bool(data.get('context')),
                    'query_type': data.get('query_type', 'unknown')
                }
            }
            
            agent_in_logger.info(f"Sent data to {agent_name}: {transfer_event['data_summary']}")
            
            # Store the transfer event as an embedding for tracking
            content = f"Data transfer to {agent_name}: {len(data.get('memories', []))} memories for {data.get('query_type', 'unknown')} query"
            vector = embed_text(content)
            
            metadata = {
                'content_type': 'agent_data_transfer',
                'source': 'agent_input_handler',
                'target_agent': agent_name,
                'transfer_summary': transfer_event['data_summary'],
                'importance_score': 0.3
            }
            
            embedding = package_embedding(content, vector, metadata)
            store_embedding(embedding)
            
            return True
            
        except Exception as e:
            agent_in_logger.error(f"Error sending data to {agent_name}: {e}")
            return False
    
    def process_agent_request(self, agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a memory request from an agent"""
        try:
            query_type = request.get('query_type', 'general')
            context = request.get('context', {})
            limit = request.get('limit', 10)
            
            # Retrieve relevant memories
            memories = self.retrieve_agent_memory(agent_name, query_type, context)
            
            # Prepare response
            response = {
                'success': True,
                'agent_name': agent_name,
                'query_type': query_type,
                'memories': memories,
                'context': context,
                'metadata': {
                    'retrieval_timestamp': datetime.now(timezone.utc).isoformat(),
                    'memory_count': len(memories),
                    'cache_hit': len(memories) > 0,
                    'retrieval_stats': self.retrieval_stats.copy()
                }
            }
            
            # Send data to agent
            self.send_data_to_agent(agent_name, response)
            
            return response
            
        except Exception as e:
            agent_in_logger.error(f"Error processing request from {agent_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_name': agent_name,
                'memories': []
            }
    
    def get_memory_system_status(self) -> Dict[str, Any]:
        """Get status of memory system and retrieval statistics"""
        try:
            backend_status = get_backend_status()
            
            return {
                'agent_input_handler': {
                    'cache_size': len(self.memory_cache),
                    'recent_queries': len(self.recent_queries),
                    'retrieval_stats': self.retrieval_stats
                },
                'memory_backend': backend_status,
                'total_embeddings': len(get_all_embeddings(limit=1000)),
                'last_query': self.recent_queries[-1] if self.recent_queries else None
            }
            
        except Exception as e:
            agent_in_logger.error(f"Error getting memory system status: {e}")
            return {'error': str(e)}
    
    def clear_cache(self):
        """Clear memory cache"""
        try:
            self.memory_cache.clear()
            agent_in_logger.info("Memory cache cleared")
        except Exception as e:
            agent_in_logger.error(f"Error clearing cache: {e}")

# Global input handler instance
input_handler = AgentInputHandler()

# Export main functions
def retrieve_agent_memory(agent_name: str, query_type: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Retrieve relevant memories for a specific agent"""
    return input_handler.retrieve_agent_memory(agent_name, query_type, context)

def process_agent_request(agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """Process a memory request from an agent"""
    return input_handler.process_agent_request(agent_name, request)

def send_data_to_agent(agent_name: str, data: Dict[str, Any]) -> bool:
    """Send data to specific agent"""
    return input_handler.send_data_to_agent(agent_name, data)

def get_memory_system_status() -> Dict[str, Any]:
    """Get memory system status"""
    return input_handler.get_memory_system_status()

def clear_cache():
    """Clear memory cache"""
    input_handler.clear_cache()

# Initialize on import
try:
    agent_in_logger.info("Agent input handler initialized and ready")
except Exception as e:
    agent_in_logger.error(f"Error initializing agent input handler: {e}")

if __name__ == "__main__":
    # Test the system
    agent_in_logger.info("Testing Agent Input Handler...")
    
    # Test memory retrieval
    test_memories = retrieve_agent_memory("strategy_agent", "trading_signals", {"symbol": "AAPL"})
    agent_in_logger.info(f"Test retrieval returned {len(test_memories)} memories")
    
    # Test status
    status = get_memory_system_status()
    agent_in_logger.info(f"Memory system status: {status}")
