"""
E2E tests for read-only mode.

Tests the MCP server with --read-only flag.
"""

import pytest
from tests.e2e.conftest import get_result_text


@pytest.mark.asyncio
async def test_list_tools(readonly_client):
    """Server exposes the query tool in read-only mode."""
    tools = await readonly_client.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "query"


@pytest.mark.asyncio
async def test_select_works(readonly_client):
    """SELECT queries work in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {"query": "SELECT 1 as num"})
    assert result.isError is False
    text = get_result_text(result)
    assert "1" in text


@pytest.mark.asyncio
async def test_query_existing_table(readonly_client):
    """Can query existing tables in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {
        "query": "SELECT * FROM users ORDER BY id LIMIT 3"
    })
    assert result.isError is False
    text = get_result_text(result)
    assert "Alice" in text


@pytest.mark.asyncio
async def test_create_table_fails(readonly_client):
    """CREATE TABLE fails in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {
        "query": "CREATE TABLE should_fail (id INT)"
    })
    assert result.isError is True
    text = get_result_text(result)
    assert "read-only" in text.lower()


@pytest.mark.asyncio
async def test_insert_fails(readonly_client):
    """INSERT fails in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {
        "query": "INSERT INTO users (id, name, email) VALUES (999, 'Test', 'test@test.com')"
    })
    assert result.isError is True
    text = get_result_text(result)
    assert "read-only" in text.lower()


@pytest.mark.asyncio
async def test_update_fails(readonly_client):
    """UPDATE fails in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {
        "query": "UPDATE users SET name = 'Modified' WHERE id = 1"
    })
    assert result.isError is True
    text = get_result_text(result)
    assert "read-only" in text.lower()


@pytest.mark.asyncio
async def test_delete_fails(readonly_client):
    """DELETE fails in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {
        "query": "DELETE FROM users WHERE id = 1"
    })
    assert result.isError is True
    text = get_result_text(result)
    assert "read-only" in text.lower()


@pytest.mark.asyncio
async def test_drop_table_fails(readonly_client):
    """DROP TABLE fails in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {
        "query": "DROP TABLE users"
    })
    assert result.isError is True
    text = get_result_text(result)
    assert "read-only" in text.lower()


@pytest.mark.asyncio
async def test_aggregate_queries_work(readonly_client):
    """Aggregate queries work in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {
        "query": "SELECT COUNT(*) as cnt FROM users"
    })
    assert result.isError is False
    text = get_result_text(result)
    assert "3" in text  # 3 users in test data


@pytest.mark.asyncio
async def test_complex_read_query(readonly_client):
    """Complex read queries work in read-only mode."""
    result = await readonly_client.call_tool_mcp("query", {
        "query": """
            WITH user_stats AS (
                SELECT COUNT(*) as total FROM users
            )
            SELECT * FROM user_stats
        """
    })
    assert result.isError is False
    text = get_result_text(result)
    assert "3" in text
