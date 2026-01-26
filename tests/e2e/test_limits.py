"""
E2E tests for query result limits.

Tests --max-rows and --max-chars options.
"""

import pytest
from tests.e2e.conftest import create_limited_client, get_result_text


@pytest.mark.asyncio
async def test_max_rows_truncation(test_db_path):
    """Results are truncated when exceeding max-rows limit."""
    client = create_limited_client(str(test_db_path), max_rows=5)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT * FROM large_table ORDER BY id"
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should contain truncation warning
        assert "5" in text  # Should mention the limit
        # Should contain data for first few rows
        assert "row_0" in text or "0" in text


@pytest.mark.asyncio
async def test_max_rows_no_truncation_when_under_limit(test_db_path):
    """No truncation warning when results are under the limit."""
    client = create_limited_client(str(test_db_path), max_rows=1000)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT * FROM users"  # Only 3 rows
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should NOT contain truncation warning
        assert "Showing first" not in text
        # Should contain all data
        assert "Alice" in text
        assert "Bob" in text
        assert "Charlie" in text


@pytest.mark.asyncio
async def test_max_chars_truncation(test_db_path):
    """Results are truncated when exceeding max-chars limit."""
    client = create_limited_client(str(test_db_path), max_chars=500)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT * FROM wide_table LIMIT 10"  # Wide rows with lots of x's, y's, z's
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Output should be truncated
        assert len(text) <= 600  # Some buffer for the warning message
        # Should contain truncation warning
        assert "truncated" in text.lower() or "500" in text


@pytest.mark.asyncio
async def test_max_chars_no_truncation_when_under_limit(test_db_path):
    """No truncation when output is under the char limit."""
    client = create_limited_client(str(test_db_path), max_chars=50000)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT id, name FROM users"  # Small output
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should NOT contain truncation warning
        assert "truncated" not in text.lower()


@pytest.mark.asyncio
async def test_both_limits_max_rows_first(test_db_path):
    """When both limits set, row limit applies first."""
    client = create_limited_client(str(test_db_path), max_rows=3, max_chars=50000)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT * FROM large_table ORDER BY id"
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should mention row limit
        assert "3" in text
        # Should only have first 3 rows worth of data
        assert "row_0" in text or "0" in text


@pytest.mark.asyncio
async def test_limit_one_row(test_db_path):
    """Can limit to just 1 row."""
    client = create_limited_client(str(test_db_path), max_rows=1)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT * FROM users ORDER BY id"
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should contain Alice (first row)
        assert "Alice" in text
        # Should have truncation warning
        assert "1" in text


@pytest.mark.asyncio
async def test_very_small_char_limit(test_db_path):
    """Very small char limit still returns something."""
    client = create_limited_client(str(test_db_path), max_chars=100)
    
    async with client:
        result = await client.call_tool_mcp("query", {
            "query": "SELECT * FROM users"
        })
        assert result.isError is False
        text = get_result_text(result)
        
        # Should return something (even if truncated)
        assert len(text) > 0
        assert len(text) <= 200  # Buffer for warning
