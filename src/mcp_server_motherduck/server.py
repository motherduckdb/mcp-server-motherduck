"""
FastMCP Server for MotherDuck and DuckDB.

This module creates and configures the FastMCP server with all tools.
"""

import json
import logging

from fastmcp import FastMCP

from .configs import SERVER_VERSION
from .database import DatabaseClient
from .instructions import get_instructions
from .tools.list_columns import list_columns as list_columns_fn
from .tools.list_databases import list_databases as list_databases_fn
from .tools.list_tables import list_tables as list_tables_fn
from .tools.query import query as query_fn
from .tools.switch_database_connection import (
    switch_database_connection as switch_database_connection_fn,
)

logger = logging.getLogger("mcp_server_motherduck")


def create_mcp_server(
    db_path: str,
    motherduck_token: str | None = None,
    home_dir: str | None = None,
    saas_mode: bool = False,
    read_only: bool = False,
    ephemeral_connections: bool = True,
    max_rows: int = 1024,
    max_chars: int = 50000,
    query_timeout: int = -1,
    init_sql: str | None = None,
    allow_switch_databases: bool = False,
    secure_mode: bool = False,
) -> FastMCP:
    """
    Create and configure the FastMCP server.

    Args:
        db_path: Path to database (local file, :memory:, md:, or s3://)
        motherduck_token: MotherDuck authentication token
        home_dir: Home directory for DuckDB
        saas_mode: Enable MotherDuck SaaS mode
        read_only: Enable read-only mode
        ephemeral_connections: Use temporary connections for read-only local files
        max_rows: Maximum rows to return from queries
        max_chars: Maximum characters in query results
        query_timeout: Query timeout in seconds (-1 to disable)
        init_sql: SQL file path or string to execute on startup
        allow_switch_databases: Enable the switch_database_connection tool
        secure_mode: Enable secure mode (restricts filesystem, extensions, locks config)

    Returns:
        Configured FastMCP server instance
    """
    # Create database client
    db_client = DatabaseClient(
        db_path=db_path,
        motherduck_token=motherduck_token,
        home_dir=home_dir,
        saas_mode=saas_mode,
        read_only=read_only,
        ephemeral_connections=ephemeral_connections,
        max_rows=max_rows,
        max_chars=max_chars,
        query_timeout=query_timeout,
        init_sql=init_sql,
        secure_mode=secure_mode,
    )

    # Get instructions with connection context
    instructions = get_instructions(read_only=read_only, saas_mode=saas_mode)

    # Create FastMCP server
    mcp = FastMCP(
        name="mcp-server-motherduck",
        instructions=instructions,
        version=SERVER_VERSION,
    )

    # Define query tool annotations (dynamic based on read_only flag)
    query_annotations = {
        "readOnlyHint": read_only,
        "destructiveHint": not read_only,
        "openWorldHint": False,
    }

    # Catalog tool annotations (always read-only)
    catalog_annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    # Register query tool
    @mcp.tool(
        name="execute_query",
        description="Execute a SQL query on the DuckDB or MotherDuck database.",
        annotations=query_annotations,
    )
    def execute_query(sql: str) -> str:
        """
        Execute a SQL query on the DuckDB or MotherDuck database.

        Args:
            sql: SQL query to execute (DuckDB SQL dialect)

        Returns:
            JSON string with query results

        Raises:
            ValueError: If the query fails
        """
        result = query_fn(sql, db_client)
        if not result.get("success", True):
            # Raise exception so FastMCP marks as isError=True
            raise ValueError(json.dumps(result, indent=2, default=str))
        return json.dumps(result, indent=2, default=str)

    # Register list_databases tool
    @mcp.tool(
        name="list_databases",
        description="List all databases with their names and types.",
        annotations=catalog_annotations,
    )
    def list_databases() -> str:
        """
        List all databases available in the connection.

        Returns:
            JSON string with database list
        """
        result = list_databases_fn(db_client)
        return json.dumps(result, indent=2, default=str)

    # Register list_tables tool
    @mcp.tool(
        name="list_tables",
        description="List all tables and views in a database with their comments.",
        annotations=catalog_annotations,
    )
    def list_tables(database: str, schema: str | None = None) -> str:
        """
        List all tables and views in a database.

        Args:
            database: Database name to list tables from
            schema: Optional schema name to filter by

        Returns:
            JSON string with table/view list
        """
        result = list_tables_fn(database, db_client, schema)
        return json.dumps(result, indent=2, default=str)

    # Register list_columns tool
    @mcp.tool(
        name="list_columns",
        description="List all columns of a table or view with their types and comments.",
        annotations=catalog_annotations,
    )
    def list_columns(database: str, table: str, schema: str = "main") -> str:
        """
        List all columns of a table or view.

        Args:
            database: Database name
            table: Table or view name
            schema: Schema name (defaults to 'main')

        Returns:
            JSON string with column list
        """
        result = list_columns_fn(database, table, db_client, schema)
        return json.dumps(result, indent=2, default=str)

    # Conditionally register switch_database_connection tool
    if allow_switch_databases:
        # Store server's read_only setting for switch_database_connection
        server_read_only_mode = read_only

        @mcp.tool(
            name="switch_database_connection",
            description="Switch to a different database connection. For local files, use absolute paths only. The new connection respects the server's read-only/read-write mode.",
            annotations=catalog_annotations,
        )
        def switch_database_connection(path: str) -> str:
            """
            Switch to a different primary database.

            Args:
                path: Database path. For local files, must be an absolute path.
                      Also accepts :memory:, md:database_name, or s3:// paths.

            Returns:
                JSON string with result
            """
            result = switch_database_connection_fn(
                path=path,
                db_client=db_client,
                server_read_only=server_read_only_mode,
            )
            return json.dumps(result, indent=2, default=str)

    logger.info(f"FastMCP server created with {len(mcp._tool_manager._tools)} tools")

    return mcp
