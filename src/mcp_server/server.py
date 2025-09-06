"""
Unified MCP Server for DuckDB/MotherDuck with Plugin Architecture
Consolidates enhanced safety features with MotherDuck connectivity
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Optional, Any, Dict, List, Sequence
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
import mcp.server.stdio

from .core.configs import get_configs
from .core.database_client import UniversalDatabaseClient, QueryValidator  
from .core.prompts import get_duckdb_guidance_prompt, get_mcp_server_help_prompt
from .plugins import DatasetPlugin, get_plugin_registry


def extract_year_from_table(table_name: str) -> str:
    """Extract year from tariff table name"""
    import re
    matches = re.findall(r'20\d{2}', table_name)
    return matches[0] if matches else "Unknown"

def categorize_table(table_name: str) -> tuple[str, str]:
    """Categorize table and extract metadata"""
    table_lower = table_name.lower()
    
    if table_lower.startswith('tariff_'):
        year = extract_year_from_table(table_name)
        return "Tariff Data", f"Year: {year}"
    elif 'usitc' in table_lower:
        return "USITC Data", "US International Trade Commission"
    elif 'trade' in table_lower:
        return "Trade Data", "International trade statistics"
    elif table_lower.startswith('hs_'):
        return "HS Codes", "Harmonized System classification"
    else:
        return "Other", "General database table"


# Set up MCP request logging
def setup_mcp_request_logging(log_dir: str = "logs"):
    """Set up comprehensive MCP request logging for unified server"""
    os.makedirs(log_dir, exist_ok=True)
    
    # Create MCP request logger
    mcp_logger = logging.getLogger("mcp_requests_unified")
    mcp_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in mcp_logger.handlers[:]:
        mcp_logger.removeHandler(handler)
    
    # File handler for MCP requests
    log_file = os.path.join(log_dir, "mcp_requests_unified.log")
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    
    # Console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Detailed formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    mcp_logger.addHandler(file_handler)
    mcp_logger.addHandler(console_handler)
    
    return mcp_logger

# Initialize MCP request logger
mcp_request_logger = setup_mcp_request_logging()

class MCPUnifiedServer:
    """Unified MCP Server with plugin architecture"""
    
    def __init__(self):
        self.config = get_configs()
        self.server = Server(self.config.name)
        
        # Get database configuration from environment
        db_path = os.environ.get("DB_PATH")
        read_only = os.environ.get("READ_ONLY", "true").lower() == "true"
        
        self.db_client = UniversalDatabaseClient(
            db_path=db_path,
            read_only=read_only
        )
        self.plugins: Dict[str, DatasetPlugin] = {}
        self.query_validator = QueryValidator()
        
        # Set up logging
        logging.basicConfig(level=self.config.log_level)
        self.logger = logging.getLogger(__name__)
        self.mcp_logger = mcp_request_logger
        
    async def initialize(self):
        """Initialize server and load plugins"""
        self.logger.info(f"Initializing {self.config.name} v{self.config.version}")
        
        # Load plugins
        registry = get_plugin_registry()
        for plugin_name, plugin_class in registry.items():
            try:
                plugin_instance = plugin_class()
                self.plugins[plugin_name] = plugin_instance
                self.logger.info(f"Loaded plugin: {plugin_name}")
            except Exception as e:
                self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
        
        # Connect to database
        await self.db_client.connect()
        
        # Register handlers
        self._register_core_handlers()
        self._register_plugin_handlers()
        
    def _register_core_handlers(self):
        """Register core MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List all available tools from core and plugins"""
            self.mcp_logger.info("MCP REQUEST: list_tools() called")
            tools = [
                types.Tool(
                    name="query_database",
                    description="Execute a safe SELECT query on the database. Query is automatically validated and limited for safety. Only read operations (SELECT, WITH, SHOW, DESCRIBE, EXPLAIN) are allowed.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL query to execute (DuckDB dialect). Only read operations are allowed."
                            },
                            "limit": {
                                "type": "integer", 
                                "description": "Maximum rows to return (default: 100, max: 1000)",
                                "default": 100,
                                "minimum": 1,
                                "maximum": 1000
                            },
                            "explain": {
                                "type": "boolean",
                                "description": "Whether to include execution metadata and performance information in response",
                                "default": False
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                types.Tool(
                    name="list_tables", 
                    description="List all available tables in the database with intelligent categorization and metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plugin": {
                                "type": "string",
                                "description": "Filter to specific plugin/dataset (optional)"
                            },
                            "include_metadata": {
                                "type": "boolean",
                                "description": "Include table metadata such as row counts and data ranges",
                                "default": False
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_schema",
                    description="Get the schema/structure of a specific table including column names, types, and constraints",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to get schema information for"
                            },
                            "include_sample": {
                                "type": "boolean",
                                "description": "Include sample values for each column to understand data patterns",
                                "default": False
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                types.Tool(
                    name="get_sample_data",
                    description="Get sample rows from a specific table to understand its structure and data patterns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to sample from"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of sample rows to return (default: 5, max: 100)",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 100
                            },
                            "random": {
                                "type": "boolean",
                                "description": "Whether to return random sample instead of first N rows",
                                "default": False
                            }
                        },
                        "required": ["table_name"]
                    }
                )
            ]
            
            # Add plugin-specific tools
            for plugin in self.plugins.values():
                tools.extend(plugin.get_specialized_tools())
            
            self.mcp_logger.info(f"MCP RESPONSE: list_tools() returning {len(tools)} tools: {[tool.name for tool in tools]}")
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls"""
            self.mcp_logger.info(f"MCP REQUEST: call_tool(name='{name}', arguments={json.dumps(arguments) if arguments else 'None'}) called")
            try:
                if name == "query_database":
                    return await self._handle_query_database(arguments)
                elif name == "list_tables":
                    return await self._handle_list_tables(arguments)
                elif name == "get_schema":
                    return await self._handle_get_schema(arguments)
                elif name == "get_sample_data":
                    return await self._handle_get_sample_data(arguments)
                else:
                    # Check plugin tools
                    return await self._handle_plugin_tool(name, arguments)
                    
            except Exception as e:
                self.logger.error(f"Tool {name} failed: {e}")
                self.mcp_logger.error(f"MCP ERROR: Tool '{name}' execution failed with exception: {str(e)}")
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error executing {name}: {str(e)}"
                )]
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[types.Prompt]:
            """List available prompts"""
            self.mcp_logger.info("MCP REQUEST: list_prompts() called")
            prompts = [
                types.Prompt(
                    name="duckdb-guidance",
                    description="Comprehensive guide for using DuckDB and understanding the database"
                ),
                types.Prompt(
                    name="mcp-help",
                    description="Help using this MCP server and understanding available tools"
                )
            ]
            
            # Add plugin prompts
            for plugin in self.plugins.values():
                prompts.extend(plugin.get_prompts())
            
            self.mcp_logger.info(f"MCP RESPONSE: list_prompts() returning {len(prompts)} prompts: {[p.name for p in prompts]}")
            return prompts
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Optional[dict] = None) -> types.GetPromptResult:
            """Handle prompt requests"""
            self.mcp_logger.info(f"MCP REQUEST: get_prompt(name='{name}', arguments={json.dumps(arguments) if arguments else 'None'}) called")
            if name == "duckdb-guidance":
                result = get_duckdb_guidance_prompt()
                self.mcp_logger.info(f"MCP RESPONSE: get_prompt() success - returning prompt for '{name}'")
                return result
            elif name == "mcp-help":
                result = get_mcp_server_help_prompt()
                self.mcp_logger.info(f"MCP RESPONSE: get_prompt() success - returning prompt for '{name}'")
                return result
            else:
                # Check plugin prompts
                for plugin in self.plugins.values():
                    plugin_prompts = plugin.get_prompts()
                    for prompt in plugin_prompts:
                        if prompt.name == name:
                            result = await self._handle_plugin_prompt(plugin, name, arguments)
                            self.mcp_logger.info(f"MCP RESPONSE: get_prompt() success - returning plugin prompt for '{name}'")
                            return result
                
                self.mcp_logger.info(f"MCP RESPONSE: get_prompt() error - unknown prompt: {name}")
                raise ValueError(f"Unknown prompt: {name}")
    
    def _register_plugin_handlers(self):
        """Register plugin-specific handlers"""
        # Plugin handlers are dynamically called through handle_call_tool
        pass
    
    async def _handle_query_database(self, arguments: dict) -> List[types.TextContent]:
        """Handle database query with validation and optional metadata"""
        sql = arguments.get("sql", "")
        limit = arguments.get("limit", 100)
        explain = arguments.get("explain", False)
        
        # Enhanced parameter validation
        if not sql or not sql.strip():
            self.mcp_logger.info("MCP RESPONSE: query_database tool - Error: Empty SQL query")
            return [types.TextContent(
                type="text",
                text="❌ Error: SQL query cannot be empty. Please provide a valid SELECT, WITH, SHOW, DESCRIBE, or EXPLAIN statement."
            )]
        
        if limit < 1 or limit > 1000:
            self.mcp_logger.info(f"MCP RESPONSE: query_database tool - Error: Invalid limit: {limit}")
            return [types.TextContent(
                type="text",
                text="❌ Error: Limit must be between 1 and 1000 rows."
            )]
        
        self.mcp_logger.info(f"MCP TOOL: query_database - Executing query: '{sql[:100]}{'...' if len(sql) > 100 else ''}' (limit={limit}, explain={explain})")
        
        # Validate query
        validation_result = self.query_validator.validate_query(sql)
        if not validation_result.is_valid:
            self.mcp_logger.info(f"MCP RESPONSE: query_database tool - Error: Query validation failed: {validation_result.error_message}")
            return [types.TextContent(
                type="text",
                text=f"❌ Query validation failed: {validation_result.error_message}\n\nAllowed operations: SELECT, WITH, SHOW, DESCRIBE, EXPLAIN"
            )]
        
        # Apply automatic limit
        modified_sql = self.query_validator.apply_limit(sql, limit)
        
        # Execute query with metadata if requested
        try:
            result = await self.db_client.execute_query(modified_sql, include_metadata=explain)
            
            response_text = f"✅ Query executed successfully:\n\n{result}"
            
            # Add query modification notice if limit was applied
            if modified_sql != sql and explain:
                response_text += f"\n\n📝 Note: Query was automatically limited to {limit} rows for safety."
            
            self.mcp_logger.info("MCP RESPONSE: query_database tool - Query executed successfully")
            return [types.TextContent(
                type="text",
                text=response_text
            )]
        except Exception as e:
            self.mcp_logger.error(f"MCP ERROR: query_database tool - Query execution failed: {str(e)}")
            return [types.TextContent(
                type="text", 
                text=f"❌ Query execution failed: {str(e)}\n\nTip: Check table names with 'list_tables' and column names with 'get_schema'."
            )]
    
    async def _handle_list_tables(self, arguments: dict) -> List[types.TextContent]:
        """Handle table listing with intelligent categorization"""
        plugin_filter = arguments.get("plugin")
        include_metadata = arguments.get("include_metadata", False)
        
        self.mcp_logger.info(f"MCP TOOL: list_tables - plugin_filter={plugin_filter}, include_metadata={include_metadata}")
        
        try:
            tables = await self.db_client.list_tables()
            
            if plugin_filter and plugin_filter in self.plugins:
                # Filter and format for specific plugin
                plugin = self.plugins[plugin_filter]
                filtered_tables = [t for t in tables if plugin.is_dataset_table(t)]
                formatted_output = plugin.format_table_list(filtered_tables)
            else:
                # Format with intelligent categorization
                formatted_output = "📋 Available Tables:\n\n"
                
                # Group tables by category
                categorized = {}
                for table in tables:
                    category, description = categorize_table(table)
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append((table, description))
                
                # Display by category
                for category, table_list in categorized.items():
                    if category == "Tariff Data":
                        formatted_output += f"🏛️ **{category}** ({len(table_list)} tables):\n"
                    elif category == "USITC Data":
                        formatted_output += f"📊 **{category}** ({len(table_list)} tables):\n"
                    elif category == "Trade Data":
                        formatted_output += f"🌍 **{category}** ({len(table_list)} tables):\n"
                    elif category == "HS Codes":
                        formatted_output += f"🏷️ **{category}** ({len(table_list)} tables):\n"
                    else:
                        formatted_output += f"🔧 **{category}** ({len(table_list)} tables):\n"
                    
                    for table, description in table_list:
                        if include_metadata:
                            formatted_output += f"  • {table} - {description}\n"
                        else:
                            formatted_output += f"  • {table}\n"
                    formatted_output += "\n"
                
                # Also show plugin categorization if available
                if self.plugins:
                    plugin_tables = []
                    for plugin_name, plugin in self.plugins.items():
                        plugin_specific = [t for t in tables if plugin.is_dataset_table(t)]
                        if plugin_specific:
                            plugin_tables.extend(plugin_specific)
                            formatted_output += f"🔌 **Plugin: {plugin_name}** ({len(plugin_specific)} tables):\n"
                            formatted_output += plugin.format_table_list(plugin_specific)
                            formatted_output += "\n"
            
            self.mcp_logger.info("MCP RESPONSE: list_tables tool - Tables listed successfully")
            return [types.TextContent(type="text", text=formatted_output)]
            
        except Exception as e:
            self.mcp_logger.error(f"MCP ERROR: list_tables tool - Failed to list tables: {str(e)}")
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to list tables: {str(e)}"
            )]
    
    async def _handle_get_schema(self, arguments: dict) -> List[types.TextContent]:
        """Handle schema requests with enhanced information"""
        table_name = arguments.get("table_name", "")
        include_sample = arguments.get("include_sample", False)
        
        # Parameter validation
        if not table_name or not table_name.strip():
            self.mcp_logger.info("MCP RESPONSE: get_schema tool - Error: Empty table name")
            return [types.TextContent(
                type="text",
                text="❌ Error: table_name cannot be empty. Use 'list_tables' to see available tables."
            )]
        
        self.mcp_logger.info(f"MCP TOOL: get_schema - table_name='{table_name}', include_sample={include_sample}")
        
        try:
            schema = await self.db_client.get_schema(table_name)
            
            # Add table categorization
            category, description = categorize_table(table_name)
            
            response_text = f"📋 Schema for **{table_name}**\n"
            response_text += f"Category: {category} - {description}\n\n"
            response_text += schema
            
            # Add sample data if requested
            if include_sample:
                try:
                    sample = await self.db_client.get_sample_data(table_name, 3)
                    response_text += f"\n\n📊 Sample Data (3 rows):\n{sample}"
                except Exception as sample_error:
                    response_text += f"\n\n⚠️ Could not retrieve sample data: {sample_error}"
            
            self.mcp_logger.info(f"MCP RESPONSE: get_schema tool - Schema retrieved successfully for '{table_name}'")
            return [types.TextContent(
                type="text",
                text=response_text
            )]
        except Exception as e:
            self.mcp_logger.error(f"MCP ERROR: get_schema tool - Failed to get schema for '{table_name}': {str(e)}")
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to get schema for {table_name}: {str(e)}\n\nTip: Use 'list_tables' to see available table names."
            )]
    
    async def _handle_get_sample_data(self, arguments: dict) -> List[types.TextContent]:
        """Handle sample data requests with enhanced options"""
        table_name = arguments.get("table_name", "")
        limit = arguments.get("limit", 5)
        random_sample = arguments.get("random", False)
        
        # Parameter validation
        if not table_name or not table_name.strip():
            self.mcp_logger.info("MCP RESPONSE: get_sample_data tool - Error: Empty table name")
            return [types.TextContent(
                type="text",
                text="❌ Error: table_name cannot be empty. Use 'list_tables' to see available tables."
            )]
        
        if limit < 1 or limit > 100:
            self.mcp_logger.info(f"MCP RESPONSE: get_sample_data tool - Error: Invalid limit: {limit}")
            return [types.TextContent(
                type="text",
                text="❌ Error: Limit must be between 1 and 100 rows."
            )]
        
        self.mcp_logger.info(f"MCP TOOL: get_sample_data - table_name='{table_name}', limit={limit}, random={random_sample}")
        
        try:
            sample = await self.db_client.get_sample_data(table_name, limit, random_sample)
            
            # Add table information
            category, description = categorize_table(table_name)
            sample_type = "random sample" if random_sample else "first rows"
            
            response_text = f"📊 Sample data from **{table_name}** ({sample_type}, limit {limit})\n"
            response_text += f"Category: {category} - {description}\n\n"
            response_text += sample
            
            self.mcp_logger.info(f"MCP RESPONSE: get_sample_data tool - Sample data retrieved successfully from '{table_name}'")
            return [types.TextContent(
                type="text",
                text=response_text
            )]
        except Exception as e:
            self.mcp_logger.error(f"MCP ERROR: get_sample_data tool - Failed to get sample data from '{table_name}': {str(e)}")
            return [types.TextContent(
                type="text", 
                text=f"❌ Failed to get sample data from {table_name}: {str(e)}\n\nTip: Use 'list_tables' to see available table names."
            )]
    
    async def _handle_plugin_tool(self, name: str, arguments: dict) -> List[types.TextContent]:
        """Handle plugin-specific tool calls"""
        # Find which plugin owns this tool
        for plugin in self.plugins.values():
            for tool in plugin.get_specialized_tools():
                if tool.name == name:
                    return await plugin.handle_tool_call(name, arguments, self.db_client)
        
        raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_plugin_prompt(self, plugin: DatasetPlugin, name: str, arguments: Optional[dict]) -> types.GetPromptResult:
        """Handle plugin-specific prompt requests"""
        return await plugin.handle_prompt_request(name, arguments)
    
    async def run_stdio(self):
        """Run server with stdio transport"""
        self.logger.info("Starting MCP Server with stdio transport")
        
        try:
            await self.initialize()
            
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.config.name,
                        server_version=self.config.version,
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(
                                prompts_changed=True,
                                resources_changed=True,
                                tools_changed=True
                            ),
                            experimental_capabilities={}
                        ),
                    ),
                )
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user (KeyboardInterrupt)")
            self.mcp_logger.info("MCP SERVER: Server stopped by user (KeyboardInterrupt)")
        except Exception as e:
            self.logger.error(f"Server failed with exception: {e}")
            self.mcp_logger.error(f"MCP SERVER: Server failed with exception: {str(e)}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up server resources")
            
            # Close database connection
            if hasattr(self.db_client, 'close'):
                self.db_client.close()
            
            # Close any plugin resources
            for plugin in self.plugins.values():
                if hasattr(plugin, 'cleanup'):
                    try:
                        await plugin.cleanup()
                    except Exception as e:
                        self.logger.warning(f"Plugin cleanup failed for {plugin.__class__.__name__}: {e}")
            
            self.mcp_logger.info("MCP SERVER: Database connection closed, server shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            self.mcp_logger.error(f"MCP SERVER: Error during cleanup: {str(e)}")

async def main():
    """Main entry point with proper resource management"""
    server = MCPUnifiedServer()
    try:
        await server.run_stdio()
    except Exception as e:
        server.logger.error(f"Fatal error: {e}")
        raise
    finally:
        # Ensure cleanup happens even if run_stdio doesn't handle it
        await server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
