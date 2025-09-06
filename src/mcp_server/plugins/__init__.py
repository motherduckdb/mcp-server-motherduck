from typing import Dict, Optional, List, Type
from abc import ABC, abstractmethod
import mcp.types as types

class DatasetPlugin(ABC):
    """Base class for dataset plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property 
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    def get_specialized_tools(self) -> list[types.Tool]:
        """Get dataset-specific tools"""
        pass
    
    @abstractmethod
    def get_prompts(self) -> list[types.Prompt]:
        """Get dataset-specific prompts"""
        pass
    
    @abstractmethod
    def is_dataset_table(self, table_name: str) -> bool:
        """Check if table belongs to this dataset"""
        pass
    
    @abstractmethod
    def extract_table_metadata(self, table_name: str) -> dict:
        """Extract metadata from table name (year, type, etc.)"""
        pass
    
    def format_table_list(self, tables: List[str]) -> str:
        """Format table list with dataset-specific information"""
        output = ""
        dataset_tables = [t for t in tables if self.is_dataset_table(t)]
        
        if dataset_tables:
            output += f"\n📊 {self.description} Tables:\n"
            for table in dataset_tables:
                metadata = self.extract_table_metadata(table)
                year = metadata.get('year', 'Unknown')
                output += f"• {table} (Year: {year})\n"
        
        return output
    
    async def handle_tool_call(self, name: str, arguments: dict, db_client) -> List[types.TextContent]:
        """Handle plugin-specific tool calls (override in subclass)"""
        return [types.TextContent(
            type="text",
            text=f"❌ Tool {name} not implemented for {self.name} plugin"
        )]
    
    async def handle_prompt_request(self, name: str, arguments: dict = None) -> types.GetPromptResult:
        """Handle plugin-specific prompt requests (override in subclass)"""
        raise ValueError(f"Prompt {name} not implemented for {self.name} plugin")

# Plugin registry - updated to use classes instead of instances
_PLUGIN_CLASSES: Dict[str, Type[DatasetPlugin]] = {}

def register_plugin(plugin_class: Type[DatasetPlugin]):
    """Register a dataset plugin class"""
    # Create temporary instance to get name
    temp_instance = plugin_class()
    _PLUGIN_CLASSES[temp_instance.name] = plugin_class

def get_plugin_registry() -> Dict[str, Type[DatasetPlugin]]:
    """Get the plugin registry"""
    return _PLUGIN_CLASSES.copy()

def get_available_datasets() -> list[str]:
    """Get list of available dataset names"""
    return list(_PLUGIN_CLASSES.keys())

def get_dataset_config(dataset_name: str) -> Optional[Type[DatasetPlugin]]:
    """Get configuration for a specific dataset"""
    return _PLUGIN_CLASSES.get(dataset_name)

def register_plugin_old(plugin: DatasetPlugin):
    """Register a dataset plugin (legacy method)"""
    register_plugin(plugin.__class__)

def format_table_list_with_datasets(tables: List[str]) -> str:
    """Format table list with all dataset-specific formatting"""
    output = "📋 Available Tables:\n\n"
    
    # Group tables by dataset
    dataset_tables = {}
    unmatched_tables = []
    
    # Create instances of plugins for table matching
    plugin_instances = {name: cls() for name, cls in _PLUGIN_CLASSES.items()}
    
    for table in tables:
        matched = False
        for plugin in plugin_instances.values():
            if plugin.is_dataset_table(table):
                if plugin.name not in dataset_tables:
                    dataset_tables[plugin.name] = []
                dataset_tables[plugin.name].append(table)
                matched = True
                break
        
        if not matched:
            unmatched_tables.append(table)
    
    # Format dataset tables
    for dataset_name, plugin_class in _PLUGIN_CLASSES.items():
        if dataset_name in dataset_tables:
            plugin_instance = plugin_class()
            output += plugin_instance.format_table_list(dataset_tables[dataset_name])
    
    # Format unmatched tables
    if unmatched_tables:
        output += "\n📄 Other Tables:\n"
        for table in unmatched_tables:
            output += f"• {table}\n"
    
    output += f"\n📊 Total: {len(tables)} tables"
    return output

# Auto-register available plugins
def _register_available_plugins():
    try:
        from .tariffs import TariffsPlugin
        register_plugin(TariffsPlugin)
    except ImportError:
        pass

_register_available_plugins()
