"""
E2E tests for local DuckDB file connections.

Tests the MCP server with a local .duckdb file.
"""

import pytest

from tests.e2e.conftest import get_result_text


@pytest.mark.asyncio
async def test_list_tools(local_client):
    """Server exposes all tools including query."""
    tools = await local_client.list_tools()
    tool_names = {t.name for t in tools}
    assert "execute_query" in tool_names
    assert "list_tables" in tool_names
    assert "list_columns" in tool_names
    assert "list_databases" in tool_names
    assert len(tools) == 4  # execute_query, list_databases, list_tables, list_columns


@pytest.mark.asyncio
async def test_simple_select(local_client):
    """Basic SELECT query works."""
    result = await local_client.call_tool_mcp("execute_query", {"sql": "SELECT 1 as num"})
    assert result.isError is False
    text = get_result_text(result)
    assert "1" in text


@pytest.mark.asyncio
async def test_query_users_table(local_client):
    """Can query the users table from test database."""
    result = await local_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT * FROM users ORDER BY id"}
    )
    assert result.isError is False
    text = get_result_text(result)
    assert "Alice" in text
    assert "Bob" in text
    assert "Charlie" in text


@pytest.mark.asyncio
async def test_query_movies_table(local_client):
    """Can query the movies table from test database."""
    result = await local_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT COUNT(*) as cnt FROM movies"}
    )
    assert result.isError is False
    text = get_result_text(result)
    # Should have 100 movies
    assert "100" in text


@pytest.mark.asyncio
async def test_create_table(local_client):
    """Can create a new table (write operation)."""
    # Create a temporary table
    result = await local_client.call_tool_mcp(
        "execute_query", {"sql": "CREATE TABLE IF NOT EXISTS test_temp (id INT, value VARCHAR)"}
    )
    assert result.isError is False

    # Verify table exists
    result = await local_client.call_tool_mcp("execute_query", {"sql": "SELECT * FROM test_temp"})
    assert result.isError is False


@pytest.mark.asyncio
async def test_insert_data(local_client):
    """Can insert data into a table."""
    # Create table first
    await local_client.call_tool_mcp(
        "execute_query", {"sql": "CREATE TABLE IF NOT EXISTS test_insert (id INT, name VARCHAR)"}
    )

    # Insert data
    result = await local_client.call_tool_mcp(
        "execute_query", {"sql": "INSERT INTO test_insert VALUES (1, 'Test')"}
    )
    assert result.isError is False

    # Verify data was inserted
    result = await local_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT * FROM test_insert WHERE id = 1"}
    )
    assert result.isError is False
    text = get_result_text(result)
    assert "Test" in text


@pytest.mark.asyncio
async def test_aggregate_query(local_client):
    """Aggregate queries work correctly."""
    result = await local_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT COUNT(*) as total, AVG(id) as avg_id FROM large_table"}
    )
    assert result.isError is False
    text = get_result_text(result)
    assert "10000" in text  # COUNT should be 10000


@pytest.mark.asyncio
async def test_invalid_query_returns_error(local_client):
    """Invalid SQL returns isError=True."""
    result = await local_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT * FROM nonexistent_table_xyz"}
    )
    assert result.isError is True
    text = get_result_text(result)
    assert "does not exist" in text.lower()


@pytest.mark.asyncio
async def test_syntax_error_returns_error(local_client):
    """SQL syntax error returns isError=True."""
    result = await local_client.call_tool_mcp("execute_query", {"sql": "SELEKT * FORM users"})
    assert result.isError is True
    text = get_result_text(result)
    assert "syntax error" in text.lower()
