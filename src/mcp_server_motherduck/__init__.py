import anyio
import logging
import click
from .server import build_application
from .configs import SERVER_VERSION, SERVER_LOCALHOST, UVICORN_LOGGING_CONFIG

__version__ = SERVER_VERSION

logger = logging.getLogger("mcp_server_motherduck")
logging.basicConfig(
    level=logging.INFO, format="[motherduck] %(levelname)s - %(message)s"
)


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option("--host", default=SERVER_LOCALHOST, help="Host to bind the MCP server")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "stream"]),
    default="stdio",
    help="(Default: `stdio`) Transport type",
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
    "--read-only",
    is_flag=True,
    help="Flag for connecting to DuckDB in read-only mode. Only supported for local DuckDB databases. Also makes use of short lived connections so multiple MCP clients or other systems can remain active (though each operation must be done sequentially).",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="(Default: `False`) Enable JSON responses instead of SSE streams. Only supported for `stream` transport.",
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
def main(
    port,
    host,
    transport,
    db_path,
    motherduck_token,
    home_dir,
    saas_mode,
    read_only,
    json_response,
    max_rows,
    max_chars,
    query_timeout,
):
    """Main entry point for the package."""

    logger.info("🦆 MotherDuck MCP Server v" + SERVER_VERSION)
    logger.info("Ready to execute SQL queries via DuckDB/MotherDuck")
    logger.info(f"Query result limits: {max_rows} rows, {max_chars:,} characters")
    if query_timeout == -1:
        logger.info("Query timeout: disabled")
    else:
        logger.info(f"Query timeout: {query_timeout}s")

    app, init_opts = build_application(
        db_path=db_path,
        motherduck_token=motherduck_token,
        home_dir=home_dir,
        saas_mode=saas_mode,
        read_only=read_only,
        max_rows=max_rows,
        max_chars=max_chars,
        query_timeout=query_timeout,
    )

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        logger.info("MCP server initialized in \033[32msse\033[0m mode")

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as (read_stream, write_stream):
                await app.run(read_stream, write_stream, init_opts)
            return Response()

        logger.info(
            f"🦆 Connect to MotherDuck MCP Server at \033[1m\033[36mhttp://{host}:{port}/sse\033[0m"
        )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(
            starlette_app,
            host=host,
            port=port,
            log_config=UVICORN_LOGGING_CONFIG,
        )

    elif transport == "stream":
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from collections.abc import AsyncIterator
        from starlette.applications import Starlette
        from starlette.routing import Mount
        from starlette.types import Receive, Scope, Send
        import contextlib

        logger.info("MCP server initialized in \033[32mhttp-streamable\033[0m mode")

        # Create the session manager with true stateless mode
        session_manager = StreamableHTTPSessionManager(
            app=app,
            event_store=None,
            json_response=json_response,
            stateless=True,
        )

        async def handle_streamable_http(
            scope: Scope, receive: Receive, send: Send
        ) -> None:
            await session_manager.handle_request(scope, receive, send)

        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            """Context manager for session manager."""
            async with session_manager.run():
                logger.info("MCP server started with StreamableHTTP session manager")
                try:
                    yield
                finally:
                    logger.info(
                        "🦆 MotherDuck MCP Server in \033[32mhttp-streamable\033[0m mode shutting down"
                    )

        logger.info(
            f"🦆 Connect to MotherDuck MCP Server at \033[1m\033[36mhttp://{host}:{port}/mcp\033[0m"
        )

        # Create an ASGI application using the transport
        starlette_app = Starlette(
            debug=True,
            routes=[
                Mount("/mcp", app=handle_streamable_http),
            ],
            lifespan=lifespan,
        )

        import uvicorn

        uvicorn.run(
            starlette_app,
            host=host,
            port=port,
            log_config=UVICORN_LOGGING_CONFIG,
        )

    else:
        from mcp.server.stdio import stdio_server

        logger.info("MCP server initialized in \033[32mstdio\033[0m mode")
        logger.info("Waiting for client connection")

        async def arun():
            async with stdio_server() as (read_stream, write_stream):
                await app.run(read_stream, write_stream, init_opts)

        try:
            anyio.run(arun)
        except (BrokenPipeError, ConnectionResetError, anyio.BrokenResourceError):
            logger.info("Client disconnected")
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except BaseException as e:
            # Handle exception groups from anyio (Python 3.11+)
            if type(e).__name__ == 'ExceptionGroup':
                if any(isinstance(exc, (BrokenPipeError, ConnectionResetError, anyio.BrokenResourceError)) 
                       for exc in getattr(e, 'exceptions', [])):
                    logger.info("Client disconnected")
                else:
                    raise
            else:
                raise
        
        # This will only be reached when the server is shutting down
        logger.info(
            "🦆 MotherDuck MCP Server in \033[32mstdio\033[0m mode shutting down"
        )


# Optionally expose other important items at package level
__all__ = ["main"]

if __name__ == "__main__":
    main()
