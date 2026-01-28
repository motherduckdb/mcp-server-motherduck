"""
E2E tests for query result limits.

Tests --max-rows and --max-chars options.
"""

import json

import pytest

from tests.e2e.conftest import create_limited_client, get_result_text


def parse_json_result(result) -> dict:
    """Parse JSON from a tool call result."""
    text = get_result_text(result)
    return json.loads(text)


@pytest.mark.asyncio
async def test_max_rows_truncation(test_db_path):
    """Results are truncated when exceeding max-rows limit."""
    client = create_limited_client(str(test_db_path), max_rows=5)

    async with client:
        result = await client.call_tool_mcp(
            "execute_query", {"sql": "SELECT * FROM large_table ORDER BY id"}
        )
        assert result.isError is False
        data = parse_json_result(result)

        # Should be marked as truncated
        assert data["success"] is True
        assert data["truncated"] is True
        assert "warning" in data
        assert data["rowCount"] == 5


@pytest.mark.asyncio
async def test_max_rows_no_truncation_when_under_limit(test_db_path):
    """No truncation warning when results are under the limit."""
    client = create_limited_client(str(test_db_path), max_rows=1000)

    async with client:
        result = await client.call_tool_mcp(
            "execute_query",
            {
                "sql": "SELECT * FROM users"  # Only 3 rows
            },
        )
        assert result.isError is False
        data = parse_json_result(result)

        # Should NOT be truncated
        assert data["success"] is True
        assert data.get("truncated") is not True
        assert data["rowCount"] == 3


@pytest.mark.asyncio
async def test_max_chars_truncation(test_db_path):
    """Results are truncated when exceeding max-chars limit."""
    client = create_limited_client(str(test_db_path), max_chars=500)

    async with client:
        result = await client.call_tool_mcp("execute_query", {"sql": "SELECT * FROM wide_table LIMIT 10"})
        assert result.isError is False
        text = get_result_text(result)

        # Output should be under the limit
        assert len(text) <= 600  # Some buffer
        data = json.loads(text)
        # Should be marked as truncated
        assert data["truncated"] is True


@pytest.mark.asyncio
async def test_max_chars_no_truncation_when_under_limit(test_db_path):
    """No truncation when output is under the char limit."""
    client = create_limited_client(str(test_db_path), max_chars=50000)

    async with client:
        result = await client.call_tool_mcp(
            "execute_query",
            {
                "sql": "SELECT id, name FROM users"  # Small output
            },
        )
        assert result.isError is False
        data = parse_json_result(result)

        # Should NOT be truncated
        assert data.get("truncated") is not True


@pytest.mark.asyncio
async def test_both_limits_max_rows_first(test_db_path):
    """When both limits set, row limit applies first."""
    client = create_limited_client(str(test_db_path), max_rows=3, max_chars=50000)

    async with client:
        result = await client.call_tool_mcp(
            "execute_query", {"sql": "SELECT * FROM large_table ORDER BY id"}
        )
        assert result.isError is False
        data = parse_json_result(result)

        # Should be truncated with 3 rows
        assert data["truncated"] is True
        assert data["rowCount"] == 3


@pytest.mark.asyncio
async def test_limit_one_row(test_db_path):
    """Can limit to just 1 row."""
    client = create_limited_client(str(test_db_path), max_rows=1)

    async with client:
        result = await client.call_tool_mcp("execute_query", {"sql": "SELECT * FROM users ORDER BY id"})
        assert result.isError is False
        data = parse_json_result(result)

        # Should have exactly 1 row
        assert data["rowCount"] == 1
        # Should be truncated
        assert data["truncated"] is True


@pytest.mark.asyncio
async def test_very_small_char_limit(test_db_path):
    """Very small char limit still returns something."""
    client = create_limited_client(str(test_db_path), max_chars=100)

    async with client:
        result = await client.call_tool_mcp("execute_query", {"sql": "SELECT * FROM users"})
        assert result.isError is False
        text = get_result_text(result)

        # Should return something (even if truncated)
        assert len(text) > 0
        # Should be valid JSON
        data = json.loads(text)
        assert data["success"] is True
