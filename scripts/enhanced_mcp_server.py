#!/usr/bin/env python3
"""
Enhanced MCP Server with proper best practices for USITC Tariff Database
"""

import logging
import json
import re
import time
from typing import Dict, List, Optional, Any
from pydantic import AnyUrl
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import duckdb

logger = logging.getLogger("enhanced_mcp_server")

class QueryValidator:
    """Validates and sanitizes SQL queries for safety"""
    
    DANGEROUS_KEYWORDS = {
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE',
        'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'EXEC', 'EXECUTE'
    }
    
    def __init__(self, max_rows: int = 1000):
        self.max_rows = max_rows
    
    def is_safe_query(self, query: str) -> tuple[bool, str]:
        """Check if query is safe for read-only operations"""
        query_upper = query.upper().strip()
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if re.search(rf'\b{keyword}\b', query_upper):
                return False, f"Query contains prohibited keyword: {keyword}"
        
        # Must start with SELECT or WITH
        if not (query_upper.startswith('SELECT') or 
                query_upper.startswith('WITH') or 
                query_upper.startswith('SHOW') or 
                query_upper.startswith('DESCRIBE')):
            return False, "Only SELECT, WITH, SHOW, and DESCRIBE queries are allowed"
        
        return True, "Query is safe"
    
    def add_limit_if_needed(self, query: str) -> str:
        """Add LIMIT clause if query doesn't have one"""
        query_upper = query.upper().strip()
        
        # Skip if already has LIMIT
        if 'LIMIT' in query_upper:
            return query
            
        # Skip for certain query types that don't need limits
        if (query_upper.startswith('SHOW') or 
            query_upper.startswith('DESCRIBE') or
            'COUNT(' in query_upper or
            'GROUP BY' in query_upper):
            return query
        
        # Add LIMIT
        return f"{query.rstrip(';')} LIMIT {self.max_rows}"

class EnhancedDatabaseClient:
    """Enhanced database client with proper connection management and safety"""
    
    def __init__(self, db_path: str, read_only: bool = True):
        self.db_path = db_path
        self.read_only = read_only
        self.validator = QueryValidator()
        self._connection = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            if self.read_only:
                self._connection = duckdb.connect(self.db_path, read_only=True)
            else:
                self._connection = duckdb.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute query with validation and error handling"""
        start_time = time.time()
        
        try:
            # Validate query
            is_safe, message = self.validator.is_safe_query(query)
            if not is_safe:
                return {
                    "success": False,
                    "error": f"Query validation failed: {message}",
                    "query": query,
                    "execution_time": 0
                }
            
            # Add LIMIT if needed
            safe_query = self.validator.add_limit_if_needed(query)
            
            # Execute query
            if not self._connection:
                self._connect()
            
            result = self._connection.execute(safe_query).fetchall()
            columns = [desc[0] for desc in self._connection.description] if self._connection.description else []
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "data": result,
                "columns": columns,
                "row_count": len(result),
                "query": safe_query,
                "original_query": query,
                "execution_time": round(execution_time, 3)
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "execution_time": round(execution_time, 3)
            }
    
    def get_schema_info(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            if table_name:
                # Get specific table schema
                query = f"DESCRIBE {table_name}"
                result = self.execute_query(query)
                if result["success"]:
                    return {
                        "success": True,
                        "table": table_name,
                        "columns": result["data"]
                    }
                return result
            else:
                # Get all tables
                query = "SHOW TABLES"
                result = self.execute_query(query)
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Schema query failed: {e}"
            }
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """Get sample data from a table"""
        query = f"SELECT * FROM {table_name} LIMIT {min(limit, 100)}"
        return self.execute_query(query)
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

def build_enhanced_server(db_path: str, read_only: bool = True):
    """Build enhanced MCP server with best practices"""
    
    logger.info("🦆 Starting Enhanced USITC Tariff MCP Server")
    server = Server("enhanced-usitc-mcp-server")
    db_client = EnhancedDatabaseClient(db_path, read_only)
    
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools with proper schemas"""
        logger.info("Listing enhanced tools")
        return [
            types.Tool(
                name="execute_query",
                description="Execute a safe SELECT query on the USITC tariff database. Query is automatically validated and limited for safety.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL SELECT query to execute (DuckDB dialect). Only read operations are allowed.",
                        },
                        "explain": {
                            "type": "boolean", 
                            "description": "Whether to include execution metadata in response",
                            "default": False
                        }
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="list_tables",
                description="List all available tables in the USITC tariff database",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="get_schema",
                description="Get the schema/structure of a specific table or all tables",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to get schema for. If not provided, returns all tables.",
                        }
                    },
                },
            ),
            types.Tool(
                name="get_sample_data",
                description="Get sample rows from a specific table to understand its structure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to sample from",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of sample rows to return (max 100)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 100
                        }
                    },
                    "required": ["table_name"],
                },
            ),
        ]
    
    @server.call_tool()
    async def handle_tool_call(
        name: str, arguments: dict | None
    ) -> list[types.TextContent]:
        """Handle tool execution with enhanced error handling"""
        logger.info(f"🔧 Calling tool: {name} with args: {arguments}")
        
        try:
            if name == "execute_query":
                if not arguments or "query" not in arguments:
                    return [types.TextContent(
                        type="text", 
                        text=json.dumps({
                            "success": False,
                            "error": "Query parameter is required"
                        }, indent=2)
                    )]
                
                result = db_client.execute_query(arguments["query"])
                
                # Format response
                if result["success"]:
                    # Create formatted table output
                    if result["data"] and result["columns"]:
                        # Format as table
                        output = format_query_result(result)
                        
                        # Add metadata if requested
                        if arguments.get("explain", False):
                            output += f"\n\n📊 Execution Info:\n"
                            output += f"• Rows returned: {result['row_count']}\n"
                            output += f"• Execution time: {result['execution_time']}s\n"
                            if result["query"] != result["original_query"]:
                                output += f"• Query was automatically limited for safety\n"
                    else:
                        output = "Query executed successfully but returned no data."
                else:
                    output = f"❌ Query failed: {result['error']}"
                
                return [types.TextContent(type="text", text=output)]
            
            elif name == "list_tables":
                result = db_client.get_schema_info()
                if result["success"]:
                    tables = [row[0] for row in result["data"]]
                    output = "📋 Available Tables:\n\n"
                    for table in tables:
                        if table.startswith("tariff_"):
                            year = extract_year_from_table(table)
                            output += f"• {table} (Year: {year})\n"
                        else:
                            output += f"• {table}\n"
                    output += f"\n📊 Total: {len(tables)} tables"
                else:
                    output = f"❌ Failed to list tables: {result['error']}"
                
                return [types.TextContent(type="text", text=output)]
            
            elif name == "get_schema":
                table_name = arguments.get("table_name") if arguments else None
                result = db_client.get_schema_info(table_name)
                
                if result["success"]:
                    if table_name:
                        output = f"📋 Schema for table '{table_name}':\n\n"
                        for row in result["data"]:
                            output += f"• {row[0]} ({row[1]})\n"
                    else:
                        output = format_query_result(result)
                else:
                    output = f"❌ Schema query failed: {result['error']}"
                
                return [types.TextContent(type="text", text=output)]
            
            elif name == "get_sample_data":
                if not arguments or "table_name" not in arguments:
                    return [types.TextContent(
                        type="text",
                        text="❌ table_name parameter is required"
                    )]
                
                table_name = arguments["table_name"]
                limit = arguments.get("limit", 5)
                result = db_client.get_sample_data(table_name, limit)
                
                if result["success"]:
                    output = f"📋 Sample data from '{table_name}' ({result['row_count']} rows):\n\n"
                    output += format_query_result(result)
                else:
                    output = f"❌ Failed to get sample data: {result['error']}"
                
                return [types.TextContent(type="text", text=output)]
            
            else:
                return [types.TextContent(
                    type="text", 
                    text=f"❌ Unknown tool: {name}"
                )]
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Tool execution failed: {str(e)}"
            )]
    
    # Set up initialization options
    initialization_options = InitializationOptions(
        server_name="enhanced-usitc-mcp-server",
        server_version="1.0.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )
    
    return server, initialization_options, db_client

def format_query_result(result: Dict[str, Any]) -> str:
    """Format query result as a nice table"""
    if not result["data"] or not result["columns"]:
        return "No data returned."
    
    data = result["data"]
    columns = result["columns"]
    
    # Calculate column widths
    widths = [len(col) for col in columns]
    for row in data[:10]:  # Only check first 10 rows for performance
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))
    
    # Limit column widths to prevent very wide tables
    widths = [min(w, 30) for w in widths]
    
    # Create table
    output = ""
    
    # Header
    header = "| " + " | ".join(f"{col:<{widths[i]}}" for i, col in enumerate(columns)) + " |"
    separator = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    
    output += header + "\n" + separator + "\n"
    
    # Rows (limit to reasonable number)
    max_rows = min(len(data), 50)
    for row in data[:max_rows]:
        formatted_row = []
        for i, value in enumerate(row):
            str_value = str(value) if value is not None else ""
            if len(str_value) > widths[i]:
                str_value = str_value[:widths[i]-3] + "..."
            formatted_row.append(f"{str_value:<{widths[i]}}")
        
        output += "| " + " | ".join(formatted_row) + " |\n"
    
    if len(data) > max_rows:
        output += f"\n... and {len(data) - max_rows} more rows\n"
    
    return output

def extract_year_from_table(table_name: str) -> str:
    """Extract year from table name"""
    matches = re.findall(r'20\d{2}', table_name)
    return matches[0] if matches else "Unknown"

if __name__ == "__main__":
    import argparse
    import uvicorn
    from mcp.server.stdio import stdio_server
    
    parser = argparse.ArgumentParser(description="Enhanced USITC Tariff MCP Server")
    parser.add_argument("--db-path", required=True, help="Path to DuckDB database")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "stream"], help="Transport mode")
    parser.add_argument("--port", type=int, default=8000, help="Port for stream transport")
    parser.add_argument("--read-only", action="store_true", help="Read-only mode")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Build server
    server, init_options, db_client = build_enhanced_server(args.db_path, args.read_only)
    
    try:
        if args.transport == "stdio":
            import asyncio
            asyncio.run(stdio_server(server, init_options))
        else:
            # Stream mode (HTTP)
            from mcp.server.session import ServerSession
            from mcp.server.sse import SseServerTransport
            
            # This would need additional implementation for HTTP transport
            print(f"🚀 Enhanced MCP Server starting on port {args.port}")
            
    except KeyboardInterrupt:
        logger.info("Server stopped")
    finally:
        db_client.close()