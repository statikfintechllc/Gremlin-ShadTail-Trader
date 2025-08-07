"""
Grok Plugin for Gremlin ShadTail Trader
Provides chat interface and AI assistance through Grok API
"""

# Import ALL dependencies through globals.py (required)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from Gremlin_Trade_Core.globals import (
    # Type imports
    Dict, Any, List, Optional,
    # Core imports
    json, asyncio, httpx, datetime, timezone,
    # Configuration and utilities
    logger, CFG
)

from ..import BasePlugin

class GrokPlugin(BasePlugin):
    """Grok AI chat plugin"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = ""
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-beta"
        self.max_tokens = 4000
        self.chat_history: List[Dict[str, Any]] = []
        self.client = None
    
    def initialize(self) -> bool:
        """Initialize Grok plugin"""
        try:
            # Load API configuration
            full_config = CFG.get("full_spec", {})
            grok_config = full_config.get("api_keys", {}).get("grok", {})
            
            self.api_key = grok_config.get("api_key", "")
            self.base_url = grok_config.get("base_url", self.base_url)
            self.model = grok_config.get("model", self.model)
            self.max_tokens = grok_config.get("max_tokens", self.max_tokens)
            
            if not self.api_key:
                self.logger.warning("Grok API key not configured - using mock responses")
            
            # Initialize HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                timeout=30.0
            )
            
            self.logger.info("Grok plugin initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Grok plugin: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown Grok plugin"""
        try:
            if self.client:
                asyncio.create_task(self.client.aclose())
            self.logger.info("Grok plugin shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error shutting down Grok plugin: {e}")
            return False
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """Return FastAPI routes for Grok plugin"""
        return [
            {
                "path": "/api/grok/chat",
                "method": "POST",
                "handler": self.chat_endpoint,
                "description": "Send message to Grok AI"
            },
            {
                "path": "/api/grok/history",
                "method": "GET",
                "handler": self.get_chat_history,
                "description": "Get chat history"
            },
            {
                "path": "/api/grok/clear",
                "method": "POST",
                "handler": self.clear_chat_history,
                "description": "Clear chat history"
            }
        ]
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI component definitions"""
        return {
            "chat": {
                "type": "chat",
                "title": "Grok AI Assistant",
                "icon": "message-circle",
                "component": "GrokChat",
                "features": [
                    "Real-time chat with Grok AI",
                    "Trading strategy assistance",
                    "Market analysis queries",
                    "Code generation and debugging"
                ]
            }
        }
    
    async def chat_endpoint(self, request):
        """Handle chat requests to Grok API"""
        try:
            data = await request.json()
            message = data.get("message", "")
            context = data.get("context", "trading")
            
            if not message:
                return {"error": "Message is required"}
            
            # Add user message to history
            user_message = {
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.chat_history.append(user_message)
            
            # Get AI response
            response = await self._get_grok_response(message, context)
            
            # Add AI response to history
            ai_message = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.chat_history.append(ai_message)
            
            # Limit history size
            max_history = self.config.get("chat_history_limit", 100)
            if len(self.chat_history) > max_history:
                self.chat_history = self.chat_history[-max_history:]
            
            return {
                "response": response,
                "timestamp": ai_message["timestamp"],
                "model": self.model
            }
            
        except Exception as e:
            self.logger.error(f"Error in chat endpoint: {e}")
            return {"error": f"Chat request failed: {str(e)}"}
    
    async def get_chat_history(self, request):
        """Get chat history"""
        try:
            limit = int(request.query_params.get("limit", 50))
            return {
                "history": self.chat_history[-limit:] if limit > 0 else self.chat_history,
                "total_messages": len(self.chat_history)
            }
        except Exception as e:
            self.logger.error(f"Error getting chat history: {e}")
            return {"error": str(e)}
    
    async def clear_chat_history(self, request):
        """Clear chat history"""
        try:
            self.chat_history.clear()
            return {"message": "Chat history cleared successfully"}
        except Exception as e:
            self.logger.error(f"Error clearing chat history: {e}")
            return {"error": str(e)}
    
    async def _get_grok_response(self, message: str, context: str = "trading") -> str:
        """Get response from Grok API"""
        try:
            if not self.api_key:
                # Mock response for development
                return self._get_mock_response(message, context)
            
            # Prepare system message based on context
            system_message = self._get_system_message(context)
            
            # Prepare messages for API
            messages = [{"role": "system", "content": system_message}]
            
            # Add recent chat history for context
            recent_history = self.chat_history[-10:] if len(self.chat_history) > 10 else self.chat_history
            messages.extend([{"role": msg["role"], "content": msg["content"]} for msg in recent_history])
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API request
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                self.logger.error(f"Grok API error: {response.status_code} - {response.text}")
                return "Sorry, I'm having trouble connecting to Grok AI right now. Please try again later."
                
        except Exception as e:
            self.logger.error(f"Error getting Grok response: {e}")
            return f"Error: {str(e)}"
    
    def _get_system_message(self, context: str) -> str:
        """Get system message based on context"""
        if context == "trading":
            return """You are Grok, an AI assistant specialized in trading and financial analysis for the Gremlin ShadTail Trader platform. 
            You help users with:
            - Trading strategy development and analysis
            - Market data interpretation
            - Risk management advice
            - Technical indicator analysis
            - Code debugging for trading algorithms
            - General trading education
            
            Be concise, accurate, and always remind users that this is not financial advice."""
        
        elif context == "coding":
            return """You are Grok, an AI assistant helping with code development for the Gremlin ShadTail Trader platform.
            You assist with:
            - Python trading algorithm development
            - FastAPI backend development
            - React/TypeScript frontend development
            - Debugging and optimization
            - Best practices and architecture advice
            
            Provide clear, working code examples when possible."""
        
        else:
            return """You are Grok, an AI assistant for the Gremlin ShadTail Trader platform. 
            You provide helpful, accurate, and concise responses to user queries."""
    
    def _get_mock_response(self, message: str, context: str) -> str:
        """Generate mock response for development/testing"""
        responses = [
            f"Thanks for your message about '{message}'. I'm currently in development mode and would normally process this through the Grok API.",
            f"That's an interesting question about '{message}'. In a real deployment, I'd analyze this using Grok's advanced AI capabilities.",
            f"I understand you're asking about '{message}'. This would typically be handled by Grok AI with full market context and trading expertise.",
        ]
        
        import random
        base_response = random.choice(responses)
        
        if context == "trading":
            base_response += " For trading-related queries, I'd provide market analysis and strategy insights."
        elif context == "coding":
            base_response += " For coding questions, I'd offer detailed code examples and debugging help."
        
        return base_response