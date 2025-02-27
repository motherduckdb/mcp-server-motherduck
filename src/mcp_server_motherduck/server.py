import os
import logging
import duckdb
from pydantic import AnyUrl
from typing import Literal
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from .prompt import PROMPT_TEMPLATE

SERVER_VERSION = "0.2.2"

logger = logging.getLogger("mcp_server_motherduck")
logger.info("Starting MCP MotherDuck Server")


class DuckDBDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.conn: duckdb.DuckDBPyConnection | None = None

        self.db_type: Literal["duckdb", "motherduck"] | None = None

    def initialize_database(self, db_path: str = None) -> None:
        """Initialize connection to the DuckDB database"""
        if self.conn is None:
            if db_path is None and os.getenv("motherduck_token"):
                db_path = "md:"

            # Check if the db_path is a local file and exists
            if not db_path.startswith("md:") and not os.path.exists(db_path):
                raise FileNotFoundError(
                    f"The database path `{db_path}` does not exist."
                )
            if db_path.startswith("md:"):
                if not os.getenv("motherduck_token"):
                    raise ValueError(
                        "Please set the `motherduck_token` environment variable."
                    )
                self.db_type = "motherduck"
            else:
                self.db_type = "duckdb"

            self.conn = duckdb.connect(
                db_path,
                config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
            )

    def query(self, query: str) -> str:
        try:
            self.initialize_database()
            return str(self.conn.execute(query).fetchall())
        except Exception as e:
            logger.error(f"Database error executing query: {e}")
            raise ValueError(f"Error executing query: {e}")


async def main():
    server = Server("mcp-server-motherduck")
    database = DuckDBDatabase()

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        """
        List available note resources.
        Each note is exposed as a resource with a custom note:// URI scheme.
        """
        return []

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        """
        Read a specific note's content by its URI.
        The note name is extracted from the URI host component.
        """
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """
        List available prompts.
        Each prompt can have optional arguments to customize its behavior.
        """
        # TODO: Check where and how this is used, and how to optimize this.
        # Check postgres and sqlite servers.
        return [
            types.Prompt(
                name="duckdb-motherduck-initial-prompt",
                description="A prompt to initialize a connection to duckdb or motherduck and start working with it",
            )
        ]

    @server.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        """
        Generate a prompt by combining arguments with server state.
        The prompt includes all current notes and can be customized via arguments.
        """
        # TODO: Check where and how this is used, and how to optimize this.
        # Check postgres and sqlite servers.
        if name != "duckdb-motherduck-initial-prompt":
            raise ValueError(f"Unknown prompt: {name}")

        return types.GetPromptResult(
            description="Initial prompt for interacting with DuckDB/MotherDuck",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=PROMPT_TEMPLATE),
                )
            ],
        )

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """
        List available tools.
        Each tool specifies its arguments using JSON Schema validation.
        """
        return [
            types.Tool(
                name="initialize-connection",
                description="Create a connection to either a local DuckDB or MotherDuck and retrieve available databases",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Type of the database, either 'DuckDB' or 'MotherDuck'",
                        },
                    },
                    "required": ["type"],
                },
            ),
            types.Tool(
                name="read-schemas",
                description="Get table schemas from a specific DuckDB/MotherDuck database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "type": {
                            "database_name": "string",
                            "description": "name of the database",
                        },
                    },
                    "required": ["database_name"],
                },
            ),
            types.Tool(
                name="execute-query",
                description="Execute a query on the MotherDuck (DuckDB) database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute",
                        },
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="query",
                description="Execute a query on the MotherDuck (DuckDB) database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_tool_call(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests.
        Tools can modify server state and notify clients of changes.
        """
        try:
            if name == "initialize-connection":
                query_result = database.query(
                    """
                    SELECT string_agg(database_name, ',\n')
                    from duckdb_databases() where database_name 
                    not in ('system', 'temp')
                    """
                ).fetchone()[0]
                tool_response = f"Connection to {database.db_path} successfully established. Here are the available databases: \n{query_result}"
                return [types.TextContent(type="text", text=tool_response)]
            if name == "read-schemas":
                database_name = arguments["database_name"]
                query_result_tables = database.query(
                    f"""
                    SELECT string_agg(regexp_replace(sql, 'CREATE TABLE ', 'CREATE TABLE '||database_name||'.'), '\n\n') as sql 
                    FROM duckdb_tables()
                    WHERE database_name = '{database_name}'
                    """
                ).fetchone()[0]
                query_result_views = database.query(
                    f"""
                    SELECT string_agg(regexp_replace(sql, 'CREATE TABLE ', 'CREATE TABLE '||database_name||'.'), '\n\n') as sql 
                    FROM duckdb_views()
                    where schema_name not in ('information_schema', 'pg_catalog', 'localmemdb')
                    and view_name not in ('duckdb_columns','duckdb_constraints','duckdb_databases','duckdb_indexes','duckdb_schemas','duckdb_tables','duckdb_types','duckdb_views','pragma_database_list','sqlite_master','sqlite_schema','sqlite_temp_master','sqlite_temp_schema')
                    and database_name = '{database_name}'
                    """
                ).fetchone()[0]
                tool_response = f"Here are all tables: \n{query_result_tables} \n\n Here are all views: {query_result_views}"
                return [types.TextContent(type="text", text=str(tool_response))]
            if name == "execute-query":
                tool_response = database.query(arguments["query"])
                return [types.TextContent(type="text", text=str(tool_response))]
            if name == "query":
                tool_response = database.query(arguments["query"])
                return [types.TextContent(type="text", text=str(tool_response))]

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            raise ValueError(f"Error executing tool {name}: {str(e)}")

    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="motherduck",
                server_version=SERVER_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
