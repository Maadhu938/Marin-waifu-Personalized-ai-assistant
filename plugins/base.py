from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None


class Plugin(ABC):
    metadata: PluginMetadata
    
    @abstractmethod
    async def initialize(self) -> bool:
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def shutdown(self):
        pass


class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.loaded: List[str] = []
    
    async def register_plugin(self, plugin: Plugin) -> bool:
        try:
            initialized = await plugin.initialize()
            if initialized:
                self.plugins[plugin.metadata.name] = plugin
                self.loaded.append(plugin.metadata.name)
                return True
        except Exception as e:
            print(f"Failed to load plugin {plugin.metadata.name}: {e}")
        return False
    
    async def unregister_plugin(self, name: str) -> bool:
        if name in self.plugins:
            await self.plugins[name].shutdown()
            del self.plugins[name]
            self.loaded.remove(name)
            return True
        return False
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict]:
        return [
            {
                "name": p.metadata.name,
                "version": p.metadata.version,
                "description": p.metadata.description,
                "loaded": p.metadata.name in self.loaded
            }
            for p in self.plugins.values()
        ]
    
    async def execute_plugin(self, name: str, **kwargs) -> Dict[str, Any]:
        plugin = self.get_plugin(name)
        if not plugin:
            return {"success": False, "error": f"Plugin '{name}' not found"}
        return await plugin.execute(**kwargs)


class ToolPlugin(Plugin):
    """Base class for tool plugins"""
    tool_name: str = ""
    tool_description: str = ""
    tool_parameters: Dict[str, Any] = {}
    
    async def initialize(self) -> bool:
        return True
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        return await self.tool_handler(**kwargs)
    
    @abstractmethod
    async def tool_handler(self, **kwargs) -> Dict[str, Any]:
        pass
    
    async def shutdown(self):
        pass


class MemoryPlugin(Plugin):
    """Base class for memory enhancement plugins"""
    
    async def on_fact_stored(self, key: str, value: Any):
        pass
    
    async def on_reflection_created(self, summary: str, topics: List[str]):
        pass
    
    async def on_context_retrieved(self, context: str) -> str:
        return context


class IntegrationPlugin(Plugin):
    """Base class for external service integrations"""
    
    async def initialize(self) -> bool:
        return True
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def disconnect(self):
        pass