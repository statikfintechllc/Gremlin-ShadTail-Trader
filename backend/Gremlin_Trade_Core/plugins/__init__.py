"""
Plugin system for Gremlin ShadTail Trader
Provides base classes and utilities for extending functionality
"""

# Import ALL dependencies through globals.py (required)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from Gremlin_Trade_Core.globals import (
    # Type imports
    Dict, Any, List, Optional,
    # Core imports
    logging, json
)

from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.logger = logging.getLogger(f"plugin.{name}")
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """Shutdown the plugin. Return True if successful."""
        pass
    
    @abstractmethod
    def get_routes(self) -> List[Dict[str, Any]]:
        """Return FastAPI routes for this plugin"""
        pass
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI component definitions for frontend"""
        return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Return current status of the plugin"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "status": "active" if self.enabled else "disabled"
        }

class PluginManager:
    """Manages all plugins in the system"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.plugins: Dict[str, BasePlugin] = {}
        self.config_path = config_path
        self.logger = logging.getLogger("plugin.manager")
    
    def load_plugin(self, plugin_class, name: str, config: Dict[str, Any]) -> bool:
        """Load and initialize a plugin"""
        try:
            plugin = plugin_class(name, config)
            if plugin.initialize():
                self.plugins[name] = plugin
                self.logger.info(f"Plugin '{name}' loaded successfully")
                return True
            else:
                self.logger.error(f"Failed to initialize plugin '{name}'")
                return False
        except Exception as e:
            self.logger.error(f"Error loading plugin '{name}': {e}")
            return False
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin"""
        if name in self.plugins:
            try:
                if self.plugins[name].shutdown():
                    del self.plugins[name]
                    self.logger.info(f"Plugin '{name}' unloaded successfully")
                    return True
                else:
                    self.logger.error(f"Failed to shutdown plugin '{name}'")
                    return False
            except Exception as e:
                self.logger.error(f"Error unloading plugin '{name}': {e}")
                return False
        return False
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a specific plugin"""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugins"""
        return self.plugins.copy()
    
    def get_plugin_routes(self) -> List[Dict[str, Any]]:
        """Get all routes from all plugins"""
        routes = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                routes.extend(plugin.get_routes())
        return routes
    
    def get_plugin_ui_components(self) -> Dict[str, Any]:
        """Get UI components from all plugins"""
        components = {}
        for name, plugin in self.plugins.items():
            if plugin.enabled:
                components[name] = plugin.get_ui_components()
        return components
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all plugins"""
        return {
            "total_plugins": len(self.plugins),
            "enabled_plugins": len([p for p in self.plugins.values() if p.enabled]),
            "plugins": {name: plugin.get_status() for name, plugin in self.plugins.items()}
        }

# Global plugin manager instance
plugin_manager = PluginManager()