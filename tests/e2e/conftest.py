"""
Fixtures for E2E testing of the MCP server.

These tests treat the MCP server as a black box, spinning it up with various
configurations and making requests via the FastMCP client.
"""

import os
import sys
import pytest
from pathlib import Path
from typing import AsyncGenerator

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


# Paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_DB_PATH = FIXTURES_DIR / "test.duckdb"


def get_mcp_client(*args: str, env: dict | None = None) -> Client:
    """
    Create a FastMCP Client for the MCP server with given arguments.
    
    Args:
        *args: Command line arguments to pass to the server
        env: Environment variables to set
    
    Returns:
        Client configured to launch the server via stdio
    """
    # Use uv run to invoke the installed script
    # This ensures we're using the local package from the workspace
    server_args = ["run", "mcp-server-motherduck"]
    server_args.extend(args)
    
    # Merge environment
    full_env = os.environ.copy()
    # Disable MotherDuck extension logging to prevent stdout pollution in stdio transport
    full_env["motherduck_logging"] = "0"
    if env:
        full_env.update(env)
    
    # Create StdioTransport with proper configuration
    # keep_alive=False ensures subprocess is terminated when connection closes
    transport = StdioTransport(
        command="uv",
        args=server_args,
        env=full_env,
        keep_alive=False,
    )
    
    return Client(transport)


def get_result_text(result) -> str:
    """Extract text from a tool call result (CallToolResult)."""
    if hasattr(result, 'content') and result.content:
        return result.content[0].text
    return str(result)


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return FIXTURES_DIR


@pytest.fixture
def test_db_path() -> Path:
    """Return the test database path."""
    if not TEST_DB_PATH.exists():
        pytest.skip(f"Test database not found at {TEST_DB_PATH}. Run 'python tests/e2e/fixtures/create_test_db.py' first.")
    return TEST_DB_PATH


@pytest.fixture
def motherduck_token() -> str:
    """Get the MotherDuck read-write token from environment."""
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        pytest.skip("MOTHERDUCK_TOKEN not set")
    return token


@pytest.fixture
def motherduck_token_read_scaling() -> str:
    """Get the MotherDuck read-scaling token from environment."""
    token = os.environ.get("MOTHERDUCK_TOKEN_READ_SCALING")
    if not token:
        pytest.skip("MOTHERDUCK_TOKEN_READ_SCALING not set")
    return token


@pytest.fixture
async def local_client(test_db_path: Path) -> AsyncGenerator[Client, None]:
    """Create a client connected to a local DuckDB file."""
    client = get_mcp_client("--db-path", str(test_db_path))
    async with client:
        yield client


@pytest.fixture
async def memory_client() -> AsyncGenerator[Client, None]:
    """Create a client connected to an in-memory DuckDB."""
    client = get_mcp_client("--db-path", ":memory:")
    async with client:
        yield client


@pytest.fixture
async def readonly_client(test_db_path: Path) -> AsyncGenerator[Client, None]:
    """Create a client connected to a local DuckDB in read-only mode."""
    client = get_mcp_client("--db-path", str(test_db_path), "--read-only")
    async with client:
        yield client


@pytest.fixture
async def motherduck_client(motherduck_token: str) -> AsyncGenerator[Client, None]:
    """Create a client connected to MotherDuck with read-write token."""
    client = get_mcp_client(
        "--db-path", "md:",
        "--motherduck-token", motherduck_token,
    )
    async with client:
        yield client


@pytest.fixture
async def motherduck_saas_client(motherduck_token_read_scaling: str) -> AsyncGenerator[Client, None]:
    """Create a client connected to MotherDuck in SaaS mode."""
    client = get_mcp_client(
        "--db-path", "md:",
        "--motherduck-token", motherduck_token_read_scaling,
        "--saas-mode",
    )
    async with client:
        yield client


def create_limited_client(
    db_path: str,
    max_rows: int | None = None,
    max_chars: int | None = None,
    query_timeout: int | None = None,
) -> Client:
    """
    Create a client with custom limits.
    
    This is a factory function, not a fixture, because we need different
    limit values for different tests.
    """
    args = ["--db-path", db_path]
    if max_rows is not None:
        args.extend(["--max-rows", str(max_rows)])
    if max_chars is not None:
        args.extend(["--max-chars", str(max_chars)])
    if query_timeout is not None:
        args.extend(["--query-timeout", str(query_timeout)])
    
    return get_mcp_client(*args)
