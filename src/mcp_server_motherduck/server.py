import os
import logging
import duckdb
from pydantic import AnyUrl
from typing import Literal, Optional
import io
from contextlib import redirect_stdout
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from .prompt import PROMPT_TEMPLATE


SERVER_VERSION = "0.4.2"

logger = logging.getLogger("mcp_server_motherduck")


class DatabaseClient:
    def __init__(
        self,
        db_path: str | None = None,
        motherduck_token: str | None = None,
        result_format: Literal["markdown", "duckbox", "text"] = "markdown",
        home_dir: str | None = None,
        saas_mode: bool = False,
        read_only: bool = False,
    ):
        self._read_only = read_only
        self.db_path, self.db_type = self._resolve_db_path_type(
            db_path, motherduck_token, saas_mode
        )
        logger.info(f"Database client initialized in `{self.db_type}` mode")

        # Set the home directory for DuckDB
        if home_dir:
            os.environ["HOME"] = home_dir

        self.conn = self._initialize_connection()
        self.result_format = result_format

    def _initialize_connection(self) -> Optional[duckdb.DuckDBPyConnection]:
        """Initialize connection to the MotherDuck or DuckDB database"""

        logger.info(f"🔌 Connecting to {self.db_type} database")

        if self.db_type == "duckdb" and self._read_only:
            # check that we can connect, issue a `select 1` and then close + return None
            try:
                conn = duckdb.connect(
                    self.db_path,
                    config={
                        "custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"
                    },
                )
                conn.execute("SELECT 1")
                conn.close()
                return None
            except Exception as e:
                logger.error(f"❌ Read-only check failed: {e}")
                raise

        conn = duckdb.connect(
            self.db_path,
            config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
        )

        logger.info(f"✅ Successfully connected to {self.db_type} database")

        return conn

    def _resolve_db_path_type(
        self, db_path: str, motherduck_token: str | None = None, saas_mode: bool = False
    ) -> tuple[str, Literal["duckdb", "motherduck"]]:
        """Resolve and validate the database path"""
        # Handle MotherDuck paths
        if db_path.startswith("md:"):
            if motherduck_token:
                logger.info("Using MotherDuck token to connect to database `md:`")
                if saas_mode:
                    logger.info("Connecting to MotherDuck in SaaS mode")
                    return (
                        f"{db_path}?motherduck_token={motherduck_token}&saas_mode=true",
                        "motherduck",
                    )
                else:
                    return (
                        f"{db_path}?motherduck_token={motherduck_token}",
                        "motherduck",
                    )
            elif os.getenv("motherduck_token"):
                logger.info(
                    "Using MotherDuck token from env to connect to database `md:`"
                )
                return (
                    f"{db_path}?motherduck_token={os.getenv('motherduck_token')}",
                    "motherduck",
                )
            else:
                raise ValueError(
                    "Please set the `motherduck_token` as an environment variable or pass it as an argument with `--motherduck-token` when using `md:` as db_path."
                )

        if db_path == ":memory:":
            return db_path, "duckdb"

        # Handle local database paths as the last check
        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"The local database path `{db_path}` does not exist."
            )
        return db_path, "duckdb"

    def _execute(self, query: str) -> str:
        if self.conn is None:
            # open short lived readonly connection, run query, close connection, return result
            conn = duckdb.connect(
                self.db_path,
                config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
                read_only=True,
            )
            q = conn.execute(query)
        else:
            q = self.conn.execute(query)

        if self.result_format == "markdown":
            out = q.fetchdf().to_markdown()
        elif self.result_format == "duckbox":
            # Duckbox version of the output
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                q.show(max_rows=100, max_col_width=20)
            out = buffer.getvalue()
        else:
            out = str(q.fetchall())

        if self.conn is None:
            conn.close()

        return out

    def query(self, query: str) -> str:
        try:
            return self._execute(query)

        except Exception as e:
            raise ValueError(f"❌ Error executing query: {e}")


async def main(
    db_path: str,
    motherduck_token: str | None = None,
    result_format: Literal["markdown", "duckbox", "text"] = "markdown",
    home_dir: str | None = None,
    saas_mode: bool = False,
    read_only: bool = False,
):
    logger.info("Starting MotherDuck MCP Server")
    server = Server("mcp-server-motherduck")
    db_client = DatabaseClient(
        db_path=db_path,
        result_format=result_format,
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
        ]

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

            return [types.TextContent(type="text", text=f"Unsupported tool: {name}")]

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

        # This will only be reached when the server is shutting down
        logger.info("\n🦆 MotherDuck MCP Server shutting down...")
