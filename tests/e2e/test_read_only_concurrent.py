"""
E2E tests for read-only concurrent access.

Tests that read-only mode allows concurrent access to local DuckDB files.
"""

import asyncio
from pathlib import Path

import pytest

from tests.e2e.conftest import get_mcp_client, get_result_text


@pytest.fixture
def test_db_path():
    """Return the test database path."""
    path = Path(__file__).parent / "fixtures" / "test.duckdb"
    if not path.exists():
        pytest.skip(f"Test database not found at {path}")
    return path


@pytest.mark.asyncio
async def test_concurrent_readonly_connections(test_db_path):
    """
    Multiple read-only clients can access the same DuckDB file concurrently.

    This verifies that read-only mode uses short-lived connections that
    don't hold locks, allowing concurrent access.
    """
    # Create two read-only clients pointing to the same database
    client1 = get_mcp_client("--db-path", str(test_db_path), "--read-only")
    client2 = get_mcp_client("--db-path", str(test_db_path), "--read-only")

    async with client1, client2:
        # Both clients should be able to query simultaneously
        result1 = await client1.call_tool_mcp("query", {"sql": "SELECT COUNT(*) as cnt FROM users"})
        result2 = await client2.call_tool_mcp(
            "query", {"sql": "SELECT COUNT(*) as cnt FROM movies"}
        )

        assert result1.isError is False
        assert result2.isError is False

        text1 = get_result_text(result1)
        text2 = get_result_text(result2)

        # Verify both got results
        assert "3" in text1  # 3 users
        assert "100" in text2  # 100 movies


@pytest.mark.asyncio
async def test_concurrent_readonly_parallel_queries(test_db_path):
    """
    Run queries in parallel from multiple read-only clients.
    """
    client1 = get_mcp_client("--db-path", str(test_db_path), "--read-only")
    client2 = get_mcp_client("--db-path", str(test_db_path), "--read-only")
    client3 = get_mcp_client("--db-path", str(test_db_path), "--read-only")

    async with client1, client2, client3:
        # Run queries in parallel
        results = await asyncio.gather(
            client1.call_tool_mcp("query", {"sql": "SELECT * FROM users ORDER BY id LIMIT 1"}),
            client2.call_tool_mcp("query", {"sql": "SELECT * FROM users ORDER BY id LIMIT 1"}),
            client3.call_tool_mcp("query", {"sql": "SELECT * FROM users ORDER BY id LIMIT 1"}),
        )

        # All should succeed
        for result in results:
            assert result.isError is False
            text = get_result_text(result)
            assert "Alice" in text


@pytest.mark.asyncio
async def test_readonly_does_not_block_other_readonly(test_db_path):
    """
    Opening a read-only connection shouldn't block another read-only connection.
    """
    client1 = get_mcp_client("--db-path", str(test_db_path), "--read-only")

    async with client1:
        # First client queries
        result1 = await client1.call_tool_mcp("query", {"sql": "SELECT 1 as num"})
        assert result1.isError is False

        # While first client is connected, open second client
        client2 = get_mcp_client("--db-path", str(test_db_path), "--read-only")
        async with client2:
            # Second client should also be able to query
            result2 = await client2.call_tool_mcp("query", {"sql": "SELECT 2 as num"})
            assert result2.isError is False

            text2 = get_result_text(result2)
            assert "2" in text2
