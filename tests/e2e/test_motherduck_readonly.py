"""
E2E tests for MotherDuck read-only behavior.

Tests that:
- --read-only flag with a read/write token is rejected (must use read-scaling token)
- --read-only flag with a read-scaling token is allowed
"""

import pytest
from tests.e2e.conftest import get_mcp_client, get_result_text


@pytest.mark.asyncio
async def test_motherduck_readonly_with_readwrite_token_rejected(motherduck_token: str):
    """
    Using --read-only with a read/write token should fail.
    
    Users must use a read-scaling token when setting --read-only for MotherDuck.
    """
    # motherduck_token fixture provides the read/write token
    client = get_mcp_client(
        "--db-path", "md:",
        "--motherduck-token", motherduck_token,
        "--read-only",
    )
    
    # The server should fail to start - connection will be closed
    with pytest.raises(Exception):
        async with client:
            # Should not get here - server should fail to initialize
            await client.list_tools()


@pytest.mark.asyncio
async def test_motherduck_readonly_with_read_scaling_token_allowed(motherduck_token_read_scaling: str):
    """
    Using --read-only with a read-scaling token should work.
    """
    client = get_mcp_client(
        "--db-path", "md:",
        "--motherduck-token", motherduck_token_read_scaling,
        "--read-only",
    )
    
    async with client:
        # Should work - read-scaling token with --read-only is valid
        tools = await client.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "query"
        
        # Should be able to query
        result = await client.call_tool_mcp("query", {"query": "SELECT 1 as num"})
        assert result.isError is False
        text = get_result_text(result)
        assert "1" in text


@pytest.mark.asyncio
async def test_motherduck_readonly_blocks_writes(motherduck_token_read_scaling: str):
    """
    With read-scaling token and --read-only, writes should be blocked.
    """
    client = get_mcp_client(
        "--db-path", "md:",
        "--motherduck-token", motherduck_token_read_scaling,
        "--read-only",
    )
    
    async with client:
        # Try to create a table - should fail
        result = await client.call_tool_mcp("query", {
            "query": "CREATE TABLE my_db.should_fail_readonly_test (id INT)"
        })
        assert result.isError is True
        text = get_result_text(result)
        # Should fail due to read-only/permissions
        assert "read" in text.lower() or "permission" in text.lower()
