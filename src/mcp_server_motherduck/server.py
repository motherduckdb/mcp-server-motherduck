import logging
import json
import os
from datetime import datetime
from pydantic import AnyUrl
from typing import Literal
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from .configs import SERVER_VERSION
from .database import DatabaseClient
from .prompt import PROMPT_TEMPLATE


logger = logging.getLogger("mcp_server_motherduck")

# Set up MCP request logging
def setup_mcp_request_logging(log_dir: str = "logs"):
    """Set up comprehensive MCP request logging for MotherDuck server"""
    os.makedirs(log_dir, exist_ok=True)
    
    # Create MCP request logger
    mcp_logger = logging.getLogger("mcp_requests_motherduck")
    mcp_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in mcp_logger.handlers[:]:
        mcp_logger.removeHandler(handler)
    
    # File handler for MCP requests
    log_file = os.path.join(log_dir, "mcp_requests_motherduck.log")
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


def build_application(
    db_path: str,
    motherduck_token: str | None = None,
    home_dir: str | None = None,
    saas_mode: bool = False,
    read_only: bool = False,
):
    logger.info("Starting MotherDuck MCP Server")
    server = Server("mcp-server-motherduck")
    db_client = DatabaseClient(
        db_path=db_path,
        motherduck_token=motherduck_token,
        home_dir=home_dir,
        saas_mode=saas_mode,
        read_only=read_only,
    )

    logger.info("Registering handlers")

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        """
        List available note resources.
        Each note is exposed as a resource with a custom note:// URI scheme.
        """
        logger.info("No resources available to list")
        mcp_request_logger.info("MCP REQUEST: list_resources() called")
        mcp_request_logger.info("MCP RESPONSE: list_resources() returning empty list")
        return []

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        """
        Read a specific note's content by its URI.
        The note name is extracted from the URI host component.
        """
        logger.info(f"Reading resource: {uri}")
        mcp_request_logger.info(f"MCP REQUEST: read_resource(uri='{uri}') called")
        mcp_request_logger.info(f"MCP RESPONSE: read_resource() error - unsupported URI scheme")
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """
        List available prompts.
        Each prompt can have optional arguments to customize its behavior.
        """
        logger.info("Listing prompts")
        mcp_request_logger.info("MCP REQUEST: list_prompts() called")
        
        # TODO: Check where and how this is used, and how to optimize this.
        # Check postgres and sqlite servers.
        prompts = [
            types.Prompt(
                name="duckdb-motherduck-initial-prompt",
                description="A prompt to initialize a connection to duckdb or motherduck and start working with it",
            )
        ]
        
        mcp_request_logger.info(f"MCP RESPONSE: list_prompts() returning {len(prompts)} prompts: {[p.name for p in prompts]}")
        return prompts

    @server.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        """
        Generate a prompt by combining arguments with server state.
        The prompt includes all current notes and can be customized via arguments.
        """
        logger.info(f"Getting prompt: {name}::{arguments}")
        mcp_request_logger.info(f"MCP REQUEST: get_prompt(name='{name}', arguments={json.dumps(arguments) if arguments else 'None'}) called")
        
        # TODO: Check where and how this is used, and how to optimize this.
        # Check postgres and sqlite servers.
        if name != "duckdb-motherduck-initial-prompt":
            mcp_request_logger.info(f"MCP RESPONSE: get_prompt() error - unknown prompt: {name}")
            raise ValueError(f"Unknown prompt: {name}")

        result = types.GetPromptResult(
            description="Initial prompt for interacting with DuckDB/MotherDuck",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=PROMPT_TEMPLATE),
                )
            ],
        )
        
        mcp_request_logger.info(f"MCP RESPONSE: get_prompt() success - returning prompt for '{name}'")
        return result

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """
        List available tools.
        Each tool specifies its arguments using JSON Schema validation.
        """
        logger.info("Listing tools")
        mcp_request_logger.info("MCP REQUEST: list_tools() called")
        
        tools = [
            types.Tool(
                name="query",
                description="Use this to execute a query on the MotherDuck or DuckDB database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute that is a dialect of DuckDB SQL",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]
        
        mcp_request_logger.info(f"MCP RESPONSE: list_tools() returning {len(tools)} tools: {[tool.name for tool in tools]}")
        return tools

    @server.call_tool()
    async def handle_tool_call(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests.
        Tools can modify server state and notify clients of changes.
        """
        logger.info(f"Calling tool: {name}::{arguments}")
        mcp_request_logger.info(f"MCP REQUEST: call_tool(name='{name}', arguments={json.dumps(arguments) if arguments else 'None'}) called")
        
        try:
            if name == "query":
                if arguments is None:
                    error_response = [
                        types.TextContent(type="text", text="Error: No query provided")
                    ]
                    mcp_request_logger.info("MCP RESPONSE: query tool - Error: No query provided")
                    return error_response
                
                query = arguments.get("query", "")
                mcp_request_logger.info(f"MCP TOOL: query - Executing query: '{query[:100]}{'...' if len(query) > 100 else ''}'")
                
                tool_response = db_client.query(arguments["query"])
                
                mcp_request_logger.info(f"MCP RESPONSE: query tool - Query executed successfully")
                return [types.TextContent(type="text", text=str(tool_response))]

            mcp_request_logger.info(f"MCP RESPONSE: unknown tool - Unsupported tool: {name}")
            return [types.TextContent(type="text", text=f"Unsupported tool: {name}")]

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            mcp_request_logger.error(f"MCP ERROR: Tool '{name}' execution failed with exception: {str(e)}")
            raise ValueError(f"Error executing tool {name}: {str(e)}")

    initialization_options = InitializationOptions(
        server_name="motherduck",
        server_version=SERVER_VERSION,
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )

    return server, initialization_options
