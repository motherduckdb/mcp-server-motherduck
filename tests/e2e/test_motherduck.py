"""
E2E tests for MotherDuck connections.

Tests the MCP server connected to MotherDuck cloud.
Requires MOTHERDUCK_TOKEN environment variable.
"""

import pytest

from tests.e2e.conftest import get_result_text


@pytest.mark.asyncio
async def test_list_tools(motherduck_client):
    """Server exposes the query tool when connected to MotherDuck."""
    tools = await motherduck_client.list_tools()
    assert len(tools) == 4  # switch_database_connection requires --allow-switch-databases
    assert tools[0].name == "query"


@pytest.mark.asyncio
async def test_simple_select(motherduck_client):
    """Basic SELECT query works with MotherDuck."""
    result = await motherduck_client.call_tool_mcp("query", {"sql": "SELECT 1 as num"})
    assert result.isError is False
    text = get_result_text(result)
    assert "1" in text


@pytest.mark.asyncio
async def test_query_sample_data(motherduck_client):
    """Can query the sample_data database."""
    result = await motherduck_client.call_tool_mcp(
        "query", {"sql": "SELECT COUNT(*) as cnt FROM sample_data.kaggle.movies"}
    )
    assert result.isError is False
    text = get_result_text(result)
    # Should have a positive count
    assert any(char.isdigit() for char in text)


@pytest.mark.asyncio
async def test_query_hacker_news(motherduck_client):
    """Can query the Hacker News sample data."""
    result = await motherduck_client.call_tool_mcp(
        "query",
        {
            "sql": """
            SELECT type, COUNT(*) as cnt 
            FROM sample_data.hn.hacker_news 
            GROUP BY type 
            ORDER BY cnt DESC 
            LIMIT 5
        """
        },
    )
    assert result.isError is False
    text = get_result_text(result)
    # Should return some data
    assert "comment" in text.lower() or "story" in text.lower()


@pytest.mark.asyncio
async def test_list_databases(motherduck_client):
    """Can list databases in MotherDuck."""
    result = await motherduck_client.call_tool_mcp(
        "query", {"sql": "SELECT database_name FROM duckdb_databases()"}
    )
    assert result.isError is False
    text = get_result_text(result)
    # Should include sample_data
    assert "sample_data" in text


@pytest.mark.asyncio
async def test_create_table_in_my_db(motherduck_client):
    """Can create a table in my_db database."""
    # First, make sure we're using my_db
    result = await motherduck_client.call_tool_mcp("query", {"sql": "USE my_db"})
    assert result.isError is False

    # Create a test table (with unique name to avoid conflicts)
    import time

    table_name = f"e2e_test_{int(time.time())}"

    result = await motherduck_client.call_tool_mcp(
        "query", {"query": f"CREATE TABLE IF NOT EXISTS {table_name} (id INT, data VARCHAR)"}
    )
    assert result.isError is False

    # Clean up
    await motherduck_client.call_tool_mcp("query", {"query": f"DROP TABLE IF EXISTS {table_name}"})


@pytest.mark.asyncio
async def test_cross_database_query(motherduck_client):
    """Can query across databases."""
    result = await motherduck_client.call_tool_mcp(
        "query",
        {
            "sql": """
            SELECT 
                (SELECT COUNT(*) FROM sample_data.kaggle.movies) as movies_count,
                (SELECT COUNT(*) FROM sample_data.hn.hacker_news LIMIT 1) as hn_exists
        """
        },
    )
    assert result.isError is False
    text = get_result_text(result)
    assert any(char.isdigit() for char in text)


@pytest.mark.asyncio
async def test_motherduck_specific_functions(motherduck_client):
    """MotherDuck-specific functions work."""
    result = await motherduck_client.call_tool_mcp(
        "query", {"sql": "SELECT current_database() as db"}
    )
    assert result.isError is False
    text = get_result_text(result)
    # Should return database name
    assert len(text) > 0
