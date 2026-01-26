"""
E2E tests for in-memory DuckDB connections.

Tests the MCP server with :memory: database.
"""

import pytest
from tests.e2e.conftest import get_result_text


@pytest.mark.asyncio
async def test_list_tools(memory_client):
    """Server exposes the query tool."""
    tools = await memory_client.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "query"


@pytest.mark.asyncio
async def test_simple_select(memory_client):
    """Basic SELECT query works."""
    result = await memory_client.call_tool_mcp("query", {"query": "SELECT 42 as answer"})
    assert result.isError is False
    text = get_result_text(result)
    assert "42" in text


@pytest.mark.asyncio
async def test_create_and_query_table(memory_client):
    """Can create table and query it in memory."""
    # Create table
    result = await memory_client.call_tool_mcp("query", {
        "query": "CREATE TABLE test (id INT, name VARCHAR)"
    })
    assert result.isError is False
    
    # Insert data
    result = await memory_client.call_tool_mcp("query", {
        "query": "INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob')"
    })
    assert result.isError is False
    
    # Query data
    result = await memory_client.call_tool_mcp("query", {
        "query": "SELECT * FROM test ORDER BY id"
    })
    assert result.isError is False
    text = get_result_text(result)
    assert "Alice" in text
    assert "Bob" in text


@pytest.mark.asyncio
async def test_duckdb_functions(memory_client):
    """DuckDB-specific functions work."""
    result = await memory_client.call_tool_mcp("query", {
        "query": "SELECT version() as duckdb_version"
    })
    assert result.isError is False
    text = get_result_text(result)
    # Should contain version number
    assert "v" in text.lower() or "." in text


@pytest.mark.asyncio
async def test_generate_series(memory_client):
    """Can use generate_series/range function."""
    result = await memory_client.call_tool_mcp("query", {
        "query": "SELECT * FROM range(5)"
    })
    assert result.isError is False
    text = get_result_text(result)
    assert "0" in text
    assert "4" in text


@pytest.mark.asyncio
async def test_json_functions(memory_client):
    """JSON functions work."""
    result = await memory_client.call_tool_mcp("query", {
        "query": """SELECT json_extract('{"name": "test", "value": 123}', '$.name') as name"""
    })
    assert result.isError is False
    text = get_result_text(result)
    assert "test" in text


@pytest.mark.asyncio
async def test_cte_query(memory_client):
    """Common Table Expressions work."""
    result = await memory_client.call_tool_mcp("query", {
        "query": """
            WITH numbers AS (
                SELECT range as n FROM range(10)
            )
            SELECT SUM(n) as total FROM numbers
        """
    })
    assert result.isError is False
    text = get_result_text(result)
    # Sum of 0-9 = 45
    assert "45" in text


@pytest.mark.asyncio
async def test_window_functions(memory_client):
    """Window functions work."""
    result = await memory_client.call_tool_mcp("query", {
        "query": "CREATE TABLE sales (product VARCHAR, amount INT)"
    })
    assert result.isError is False
    
    result = await memory_client.call_tool_mcp("query", {
        "query": "INSERT INTO sales VALUES ('A', 100), ('A', 200), ('B', 150)"
    })
    assert result.isError is False
    
    result = await memory_client.call_tool_mcp("query", {
        "query": """
            SELECT product, amount, 
                   SUM(amount) OVER (PARTITION BY product) as product_total
            FROM sales
            ORDER BY product, amount
        """
    })
    assert result.isError is False
    text = get_result_text(result)
    assert "300" in text  # Sum for product A
    assert "150" in text  # Sum for product B
