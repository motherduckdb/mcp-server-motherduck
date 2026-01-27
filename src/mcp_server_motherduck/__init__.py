"""
MotherDuck MCP Server - A FastMCP server for DuckDB and MotherDuck.

This module provides the CLI entry point for the MCP server.
"""

import logging
import warnings

import click

from .configs import SERVER_LOCALHOST, SERVER_VERSION
from .server import create_mcp_server

__version__ = SERVER_VERSION

logger = logging.getLogger("mcp_server_motherduck")
logging.basicConfig(
    level=logging.INFO, format="[motherduck] %(levelname)s - %(message)s"
)


@click.command()
@click.option("--port", default=8000, help="Port to listen on for HTTP transport")
@click.option("--host", default=SERVER_LOCALHOST, help="Host to bind the MCP server")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http", "sse", "stream"]),
    default="stdio",
    help="(Default: `stdio`) Transport type. Use `http` for HTTP Streamable transport. `sse` and `stream` are deprecated aliases.",
)
@click.option(
    "--db-path",
    default="md:",
    help="(Default: `md:`) Path to local DuckDB database file or MotherDuck database",
)
@click.option(
    "--motherduck-token",
    default=None,
    help="(Default: env var `motherduck_token`) Access token to use for MotherDuck database connections",
)
@click.option(
    "--home-dir",
    default=None,
    help="(Default: env var `HOME`) Home directory for DuckDB",
)
@click.option(
    "--saas-mode",
    is_flag=True,
    help="Flag for connecting to MotherDuck in SaaS mode",
)
@click.option(
    "--read-write",
    is_flag=True,
    help="Enable write access to the database. By default, the server runs in read-only mode for local DuckDB files and MotherDuck databases. Note: In-memory databases are always writable (DuckDB limitation).",
)
@click.option(
    "--ephemeral-connections/--no-ephemeral-connections",
    default=True,
    help="Use temporary connections for read-only local DuckDB files, creating a new connection for each query. This keeps the file unlocked so other processes can write to it.",
)
@click.option(
    "--max-rows",
    type=int,
    default=1024,
    help="(Default: `1024`) Maximum number of rows to return from queries. Use LIMIT in your SQL for specific row counts.",
)
@click.option(
    "--max-chars",
    type=int,
    default=50000,
    help="(Default: `50000`) Maximum number of characters in query results. Prevents issues with wide rows or large text columns.",
)
@click.option(
    "--query-timeout",
    type=int,
    default=-1,
    help="(Default: `-1`) Query execution timeout in seconds. Set to -1 to disable timeout.",
)
@click.option(
    "--init-sql",
    default=None,
    help="SQL file path or SQL string to execute on startup for database initialization.",
)
@click.option(
    "--allow-switch-databases",
    is_flag=True,
    help="Enable the switch_database_connection tool to change databases at runtime. Disabled by default.",
)
def main(
    port: int,
    host: str,
    transport: str,
    db_path: str,
    motherduck_token: str | None,
    home_dir: str | None,
    saas_mode: bool,
    read_write: bool,
    ephemeral_connections: bool,
    max_rows: int,
    max_chars: int,
    query_timeout: int,
    init_sql: str | None,
    allow_switch_databases: bool,
) -> None:
    """MotherDuck MCP Server - Execute SQL queries via DuckDB/MotherDuck."""
    # Convert read_write flag to read_only (inverted logic)
    # Note: in-memory databases cannot be read-only (DuckDB limitation)
    is_memory = db_path == ":memory:"
    if is_memory and not read_write:
        logger.warning(
            "⚠️  In-memory databases cannot run in read-only mode (DuckDB limitation). "
            "Writes will be allowed."
        )
    read_only = not read_write and not is_memory

    logger.info("🦆 MotherDuck MCP Server v" + SERVER_VERSION)
    logger.info("Ready to execute SQL queries via DuckDB/MotherDuck")
    if is_memory:
        logger.info("Database mode: read-write (in-memory)")
    else:
        mode_str = "read-write" if read_write else "read-only"
        if not read_write and not ephemeral_connections:
            mode_str += " (persistent connection)"
        logger.info(f"Database mode: {mode_str}")
    logger.info(f"Query result limits: {max_rows} rows, {max_chars:,} characters")
    if query_timeout == -1:
        logger.info("Query timeout: disabled")
    else:
        logger.info(f"Query timeout: {query_timeout}s")
    if init_sql:
        logger.info("Init SQL: configured")
    if allow_switch_databases:
        logger.info("Switch databases: enabled")

    # Handle deprecated transport aliases
    if transport == "stream":
        warnings.warn(
            "The 'stream' transport is deprecated. Use 'http' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.warning(
            "⚠️  '--transport stream' is deprecated. Use '--transport http' instead."
        )
        transport = "http"
    elif transport == "sse":
        warnings.warn(
            "The 'sse' transport is deprecated. Use 'http' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.warning(
            "⚠️  '--transport sse' is deprecated. Use '--transport http' instead."
        )
        transport = "http"

    # Create the FastMCP server
    mcp = create_mcp_server(
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
        allow_switch_databases=allow_switch_databases,
    )

    # Run the server with the appropriate transport
    if transport == "http":
        logger.info("MCP server initialized in \033[32mhttp\033[0m mode")
        logger.info(
            f"🦆 Connect to MotherDuck MCP Server at \033[1m\033[36mhttp://{host}:{port}/mcp\033[0m"
        )
        mcp.run(transport="http", host=host, port=port)
    else:
        logger.info("MCP server initialized in \033[32mstdio\033[0m mode")
        logger.info("Waiting for client connection")
        mcp.run(transport="stdio")


# Optionally expose other important items at package level
__all__ = ["main", "__version__"]

if __name__ == "__main__":
    main()
