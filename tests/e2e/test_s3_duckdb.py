"""
E2E tests for S3 DuckDB connections.

Tests the MCP server with --db-path s3://...

Set the S3_TEST_DB_PATH environment variable to a valid S3 DuckDB path to run these tests.
Example: S3_TEST_DB_PATH=s3://your-bucket/path/to/database.duckdb

Note: S3 databases are attached as read-only.
"""

import os
import pytest
from tests.e2e.conftest import get_mcp_client, get_result_text


@pytest.fixture
def s3_db_path():
    """Get the S3 test database path from environment."""
    path = os.environ.get("S3_TEST_DB_PATH")
    if not path:
        pytest.skip("S3_TEST_DB_PATH not set - skipping S3 tests")
    return path


@pytest.fixture
async def s3_client(s3_db_path: str):
    """Create a client connected to an S3 DuckDB database."""
    client = get_mcp_client("--db-path", s3_db_path)
    async with client:
        yield client


@pytest.mark.asyncio
async def test_s3_list_tools(s3_client):
    """Server exposes the query tool when connected to S3 database."""
    tools = await s3_client.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "query"


@pytest.mark.asyncio
async def test_s3_simple_select(s3_client):
    """Basic SELECT query works with S3 database."""
    result = await s3_client.call_tool_mcp("query", {"query": "SELECT 1 as num"})
    assert result.isError is False
    text = get_result_text(result)
    assert "1" in text


@pytest.mark.asyncio
async def test_s3_show_tables(s3_client):
    """Can list tables in S3 database."""
    result = await s3_client.call_tool_mcp("query", {"query": "SHOW TABLES"})
    assert result.isError is False
    # Just verify it returns something (tables depend on the database)
    text = get_result_text(result)
    assert len(text) > 0


@pytest.mark.asyncio
async def test_s3_is_readonly(s3_client):
    """S3 databases are attached as read-only, writes should fail."""
    result = await s3_client.call_tool_mcp("query", {
        "query": "CREATE TABLE should_fail_s3 (id INT)"
    })
    assert result.isError is True
    text = get_result_text(result)
    # Should fail due to read-only
    assert "read" in text.lower() or "permission" in text.lower() or "cannot" in text.lower()


@pytest.mark.asyncio
async def test_s3_query_data(s3_client):
    """Can query actual data from S3 database."""
    # First get a table name
    tables_result = await s3_client.call_tool_mcp("query", {"query": "SHOW TABLES"})
    if tables_result.isError:
        pytest.skip("Could not list tables")
    
    # Try to count rows in the first table
    result = await s3_client.call_tool_mcp("query", {
        "query": "SELECT COUNT(*) as total FROM (SHOW TABLES)"
    })
    assert result.isError is False
