"""
E2E tests for MotherDuck read-only behavior.

Tests that:
- Default mode (without --read-write) is read-only
- Read-scaling tokens work in default read-only mode
- Writes are blocked in default read-only mode

Note: The server defaults to read-only mode. Use --read-write to enable writes.
"""

import pytest

from tests.e2e.conftest import get_mcp_client, get_result_text


@pytest.mark.asyncio
async def test_motherduck_readonly_rejects_readwrite_token(motherduck_token: str):
    """
    Default read-only mode with a read/write token should be rejected.

    For security, MotherDuck connections in read-only mode require a read-scaling
    token. Using a read/write token in read-only mode indicates misconfiguration.
    """
    # motherduck_token fixture provides the read/write token
    client = get_mcp_client(
        "--db-path",
        "md:",
        "--motherduck-token",
        motherduck_token,
        # No --read-write flag, so server runs in default read-only mode
    )

    # The server should fail to start - read/write token not allowed in read-only mode
    with pytest.raises(Exception):
        async with client:
            # Should not get here - server should fail to initialize
            await client.list_tools()


@pytest.mark.asyncio
async def test_motherduck_default_readonly_with_read_scaling_token(
    motherduck_token_read_scaling: str,
):
    """
    Default mode with a read-scaling token should work.
    """
    client = get_mcp_client(
        "--db-path",
        "md:",
        "--motherduck-token",
        motherduck_token_read_scaling,
        # No --read-write flag, server runs in default read-only mode
    )

    async with client:
        # Should work - read-scaling token in default read-only mode
        tools = await client.list_tools()
        assert len(tools) == 4  # switch_database_connection requires --allow-switch-databases
        assert tools[0].name == "execute_query"

        # Should be able to query
        result = await client.call_tool_mcp("execute_query", {"sql": "SELECT 1 as num"})
        assert result.isError is False
        text = get_result_text(result)
        assert "1" in text


@pytest.mark.asyncio
async def test_motherduck_default_readonly_blocks_writes(motherduck_token_read_scaling: str):
    """
    Default read-only mode should block write operations.
    """
    client = get_mcp_client(
        "--db-path",
        "md:",
        "--motherduck-token",
        motherduck_token_read_scaling,
        # No --read-write flag, server runs in default read-only mode
    )

    async with client:
        # Try to create a table - should fail due to read-only mode
        result = await client.call_tool_mcp(
            "execute_query", {"sql": "CREATE TABLE my_db.should_fail_readonly_test (id INT)"}
        )
        assert result.isError is True
        text = get_result_text(result)
        # Should fail due to read-only mode
        assert (
            "read" in text.lower() or "permission" in text.lower() or "not allowed" in text.lower()
        )
