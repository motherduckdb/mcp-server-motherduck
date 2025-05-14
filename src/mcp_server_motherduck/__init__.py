from . import server
import asyncio
import argparse
import logging

logger = logging.getLogger("mcp_server_motherduck")
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(levelname)s - %(message)s")


def main():
    """Main entry point for the package."""

    parser = argparse.ArgumentParser(description="MotherDuck MCP Server")
    parser.add_argument(
        "--db-path",
        default="md:",
        help="(Default: `md:`) Path to local DuckDB database file or MotherDuck database",
    )
    parser.add_argument(
        "--motherduck-token",
        default=None,
        help="(Default: env var `motherduck_token`) Access token to use for MotherDuck database connections",
    )
    parser.add_argument(
        "--home-dir",
        default=None,
        help="(Default: env var `HOME`) Home directory for DuckDB",
    )
    parser.add_argument(
        "--saas-mode",
        action="store_true",
        help="Flag for connecting to MotherDuck in SaaS mode",
    )
    # This is experimental and will change in the future
    parser.add_argument(
        "--result-format",
        help="(Default: `markdown`) Format of the query result",
        default="markdown",
        choices=["markdown", "duckbox", "text"],
    )

    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Flag for connecting to DuckDB in read-only mode. Only supported for local DuckDB databases.",
    )

    args = parser.parse_args()
    logger.info("🦆 MotherDuck MCP Server v" + server.SERVER_VERSION)
    logger.info("Ready to execute SQL queries via DuckDB/MotherDuck")
    logger.info("Waiting for client connection...\n")

    asyncio.run(
        server.main(
            db_path=args.db_path,
            motherduck_token=args.motherduck_token,
            result_format=args.result_format,
            home_dir=args.home_dir,
            saas_mode=args.saas_mode,
            read_only=args.read_only,
        )
    )


# Optionally expose other important items at package level
__all__ = ["main", "server"]
