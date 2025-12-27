import logging
from pydantic import AnyUrl
from typing import Literal
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from .configs import SERVER_VERSION
from .database import DatabaseClient
from .prompt import PROMPT_TEMPLATE


logger = logging.getLogger("mcp_server_motherduck")


def build_application(
    db_path: str,
    motherduck_token: str | None = None,
    home_dir: str | None = None,
    saas_mode: bool = False,
    read_only: bool = False,
    max_rows: int = 1024,
    max_chars: int = 50000,
    query_timeout: int = -1,
):
    logger.info("Starting MotherDuck MCP Server")
    server = Server("mcp-server-motherduck")
    db_client = DatabaseClient(
        db_path=db_path,
        motherduck_token=motherduck_token,
        home_dir=home_dir,
        saas_mode=saas_mode,
        read_only=read_only,
        max_rows=max_rows,
        max_chars=max_chars,
        query_timeout=query_timeout,
    )

    logger.info("Registering handlers")

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        """
        List available note resources.
        Each note is exposed as a resource with a custom note:// URI scheme.
        """
        logger.info("No resources available to list")
        return []

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        """
        Read a specific note's content by its URI.
        The note name is extracted from the URI host component.
        """
        logger.info(f"Reading resource: {uri}")
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """
        List available prompts.
        Each prompt can have optional arguments to customize its behavior.
        """
        logger.info("Listing prompts")
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
        logger.info(f"Getting prompt: {name}::{arguments}")
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
        logger.info("Listing tools")
        return [
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
            types.Tool(
                name="list_tables",
                description="List all tables in a database with properly quoted identifiers. Use this FIRST before writing queries to get correct table and column names. Returns tables with quoted names ready to use in SQL.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "Database name to list tables from. If not provided, lists tables from current database.",
                        },
                        "include_columns": {
                            "type": "boolean",
                            "description": "If true, also returns column names for each table. Default is false.",
                        },
                    },
                    "required": [],
                },
            ),
        ]

    def _quote_identifier(identifier: str) -> str:
        """Quote an identifier for safe use in SQL."""
        # Escape any existing double quotes by doubling them
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    def _needs_quoting(identifier: str) -> bool:
        """Check if an identifier needs quoting."""
        import re
        # Needs quoting if: contains special chars, starts with number, is reserved word, or has mixed case
        if not identifier:
            return True
        # Contains anything other than letters, numbers, underscores
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            return True
        # Check for reserved words (simplified list)
        reserved = {'select', 'from', 'where', 'order', 'group', 'by', 'having', 'join', 'on', 'and', 'or', 'not', 'in', 'is', 'null', 'true', 'false', 'as', 'distinct', 'all', 'union', 'except', 'intersect', 'case', 'when', 'then', 'else', 'end', 'create', 'table', 'view', 'index', 'drop', 'alter', 'insert', 'update', 'delete', 'into', 'values', 'set', 'primary', 'key', 'foreign', 'references', 'constraint', 'default', 'check', 'unique', 'limit', 'offset', 'asc', 'desc', 'nulls', 'first', 'last', 'like', 'between', 'exists', 'any', 'some'}
        if identifier.lower() in reserved:
            return True
        return False

    @server.call_tool()
    async def handle_tool_call(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests.
        Tools can modify server state and notify clients of changes.
        """
        logger.info(f"Calling tool: {name}::{arguments}")
        try:
            if name == "query":
                if arguments is None:
                    return [
                        types.TextContent(type="text", text="Error: No query provided")
                    ]
                tool_response = db_client.query(arguments["query"])
                return [types.TextContent(type="text", text=str(tool_response))]

            elif name == "list_tables":
                arguments = arguments or {}
                database = arguments.get("database")
                include_columns = arguments.get("include_columns", False)

                results = []

                # Get list of tables
                if database:
                    quoted_db = _quote_identifier(database)
                    tables_query = f"SELECT table_name FROM information_schema.tables WHERE table_catalog = '{database}' AND table_schema = 'main'"
                    use_query = f"USE {quoted_db}"
                    try:
                        db_client.query(use_query)
                    except Exception as e:
                        return [types.TextContent(type="text", text=f"Error switching to database {quoted_db}: {str(e)}")]
                else:
                    tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"

                try:
                    tables_result = db_client.query("SHOW TABLES")
                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error listing tables: {str(e)}")]

                # Parse table names from result
                lines = str(tables_result).strip().split('\n')
                table_names = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('+') and not line.startswith('|') and 'name' not in line.lower() and 'varchar' not in line.lower():
                        table_names.append(line)
                    elif line.startswith('|') and 'name' not in line.lower() and 'VARCHAR' not in line:
                        # Extract table name from formatted output like "| table_name |"
                        parts = line.split('|')
                        if len(parts) >= 2:
                            table_name = parts[1].strip()
                            if table_name and table_name != 'name':
                                table_names.append(table_name)

                output_lines = []
                output_lines.append("# Tables with Properly Quoted Identifiers")
                output_lines.append("")
                output_lines.append("Use these exact quoted names in your SQL queries to avoid binding errors.")
                output_lines.append("")

                if database:
                    output_lines.append(f"Database: {_quote_identifier(database)}")
                    output_lines.append("")

                for table_name in table_names:
                    quoted_table = _quote_identifier(table_name)
                    if database:
                        full_reference = f"{_quote_identifier(database)}.main.{quoted_table}"
                    else:
                        full_reference = quoted_table

                    output_lines.append(f"## Table: {quoted_table}")
                    output_lines.append(f"   Full reference: {full_reference}")

                    if include_columns:
                        try:
                            cols_result = db_client.query(f"DESCRIBE {quoted_table}")
                            output_lines.append("   Columns:")
                            # Parse column info
                            col_lines = str(cols_result).strip().split('\n')
                            for col_line in col_lines:
                                if col_line.startswith('|') and 'column_name' not in col_line.lower() and 'VARCHAR' not in col_line:
                                    parts = col_line.split('|')
                                    if len(parts) >= 3:
                                        col_name = parts[1].strip()
                                        col_type = parts[2].strip()
                                        if col_name:
                                            quoted_col = _quote_identifier(col_name)
                                            output_lines.append(f"     - {quoted_col} ({col_type})")
                        except Exception as e:
                            output_lines.append(f"   (Could not fetch columns: {str(e)})")

                    output_lines.append("")

                if not table_names:
                    output_lines.append("No tables found in the current database.")
                    output_lines.append("")
                    output_lines.append("Tip: Use SHOW DATABASES to see available databases, then USE \"database_name\" to switch.")

                return [types.TextContent(type="text", text="\n".join(output_lines))]

            return [types.TextContent(type="text", text=f"Unsupported tool: {name}")]

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
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
