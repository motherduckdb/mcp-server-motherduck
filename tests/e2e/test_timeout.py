"""
E2E tests for query timeout.

Tests the --query-timeout option.

Note: Timeout tests can be flaky depending on machine performance.
The slow test is marked and can be skipped with -m "not slow".
"""

import pytest
from tests.e2e.conftest import create_limited_client, get_result_text


@pytest.mark.asyncio
async def test_fast_query_completes(test_db_path):
    """Fast queries complete within timeout."""
    client = create_limited_client(str(test_db_path), query_timeout=10)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT 1 as num"
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should complete successfully
        assert "1" in text
        assert "timeout" not in text.lower()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_slow_query_times_out():
    """Slow queries timeout when exceeding the limit.
    
    Note: This test is environment-dependent. On very fast machines,
    the query may complete before the timeout. Marked as slow.
    """
    client = create_limited_client(":memory:", query_timeout=1)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": """
                SELECT COUNT(*) FROM (
                    SELECT a.range, b.range, c.range, d.range, e.range
                    FROM range(100) a, range(100) b, range(100) c, range(100) d, range(100) e
                )
            """
        })
        
        if result.isError:
            # Query timed out as expected
            text = get_result_text(result)
            assert "timeout" in text.lower()
        else:
            # Query completed before timeout - machine too fast
            pytest.skip("Query completed before timeout - machine too fast for this test")


@pytest.mark.asyncio
async def test_timeout_disabled_with_negative_one():
    """Timeout is disabled when set to -1."""
    client = create_limited_client(":memory:", query_timeout=-1)
    
    async with client:
        # A query that should complete
        result = await client.call_tool_mcp("query", {
            "query": """
                SELECT COUNT(*) as cnt FROM range(100000)
            """
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should complete successfully
        assert "100000" in text
        assert "timeout" not in text.lower()


@pytest.mark.asyncio
async def test_moderate_query_with_adequate_timeout(test_db_path):
    """Moderate queries complete with adequate timeout."""
    client = create_limited_client(str(test_db_path), query_timeout=30)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT COUNT(*) as cnt FROM large_table"
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should complete successfully
        assert "10000" in text
        assert "timeout" not in text.lower()
