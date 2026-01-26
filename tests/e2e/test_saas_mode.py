"""
E2E tests for SaaS mode.

Tests the MCP server in SaaS mode which restricts certain operations.
Requires MOTHERDUCK_TOKEN_READ_SCALING environment variable.
"""

import pytest
from tests.e2e.conftest import get_result_text


@pytest.mark.asyncio
async def test_list_tools(motherduck_saas_client):
    """Server exposes the query tool in SaaS mode."""
    tools = await motherduck_saas_client.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "query"


@pytest.mark.asyncio
async def test_simple_select(motherduck_saas_client):
    """Basic SELECT query works in SaaS mode."""
    result = await motherduck_saas_client.call_tool_mcp("query", {"query": "SELECT 1 as num"})
    assert result.isError is False
    text = get_result_text(result)
    assert "1" in text


@pytest.mark.asyncio
async def test_query_sample_data(motherduck_saas_client):
    """Can query sample_data in SaaS mode."""
    result = await motherduck_saas_client.call_tool_mcp("query", {
        "query": "SELECT COUNT(*) as cnt FROM sample_data.kaggle.movies"
    })
    assert result.isError is False
    text = get_result_text(result)
    assert any(char.isdigit() for char in text)


@pytest.mark.asyncio
async def test_create_database_blocked(motherduck_saas_client):
    """CREATE DATABASE is blocked in SaaS mode."""
    result = await motherduck_saas_client.call_tool_mcp("query", {
        "query": "CREATE DATABASE should_fail_saas"
    })
    assert result.isError is True
    text = get_result_text(result)
    # Should error - SaaS mode blocks database creation
    assert "saas" in text.lower() or "permission" in text.lower() or "not allowed" in text.lower()


@pytest.mark.asyncio
async def test_drop_database_blocked(motherduck_saas_client):
    """DROP DATABASE is blocked in SaaS mode."""
    result = await motherduck_saas_client.call_tool_mcp("query", {
        "query": "DROP DATABASE IF EXISTS should_not_exist_anyway"
    })
    assert result.isError is True
    text = get_result_text(result)
    assert "saas" in text.lower() or "permission" in text.lower() or "not allowed" in text.lower()


@pytest.mark.asyncio
async def test_read_scaling_token_is_readonly(motherduck_saas_client):
    """Read-scaling token should not allow writes to sample_data."""
    result = await motherduck_saas_client.call_tool_mcp("query", {
        "query": """
            INSERT INTO sample_data.kaggle.movies (title) VALUES ('Should Fail')
        """
    })
    assert result.isError is True
    text = get_result_text(result)
    # Should fail - can't write to shared database with read-scaling token
    assert "permission" in text.lower() or "read" in text.lower() or "not allowed" in text.lower()


@pytest.mark.asyncio
async def test_aggregate_queries_work(motherduck_saas_client):
    """Aggregate queries work in SaaS mode."""
    result = await motherduck_saas_client.call_tool_mcp("query", {
        "query": """
            SELECT type, COUNT(*) as cnt 
            FROM sample_data.hn.hacker_news 
            GROUP BY type 
            ORDER BY cnt DESC 
            LIMIT 3
        """
    })
    assert result.isError is False
    text = get_result_text(result)
    assert any(char.isdigit() for char in text)


@pytest.mark.asyncio
async def test_complex_analytical_query(motherduck_saas_client):
    """Complex analytical queries work in SaaS mode."""
    result = await motherduck_saas_client.call_tool_mcp("query", {
        "query": """
            WITH movie_stats AS (
                SELECT 
                    COUNT(*) as total_movies
                FROM sample_data.kaggle.movies
            )
            SELECT * FROM movie_stats
        """
    })
    assert result.isError is False
    text = get_result_text(result)
    assert any(char.isdigit() for char in text)
