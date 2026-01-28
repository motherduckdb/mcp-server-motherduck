"""
E2E tests for secure mode.

Tests the MCP server with --secure-mode flag which:
- Disables LocalFileSystem access
- Disables community extensions
- Locks configuration
"""

import pytest

from tests.e2e.conftest import get_result_text


@pytest.mark.asyncio
async def test_list_tools(secure_mode_client):
    """Server exposes all tools in secure mode."""
    tools = await secure_mode_client.list_tools()
    tool_names = {t.name for t in tools}
    assert "execute_query" in tool_names
    assert len(tools) == 4


@pytest.mark.asyncio
async def test_simple_select(secure_mode_client):
    """Basic SELECT query works in secure mode."""
    result = await secure_mode_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT 1 as num"}
    )
    assert result.isError is False
    text = get_result_text(result)
    assert "1" in text


@pytest.mark.asyncio
async def test_local_file_access_blocked(secure_mode_client):
    """Local file access is blocked in secure mode."""
    result = await secure_mode_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT * FROM read_csv('/etc/passwd', sep=':')"}
    )
    assert result.isError is True
    text = get_result_text(result)
    assert "LocalFileSystem" in text or "disabled" in text.lower()


@pytest.mark.asyncio
async def test_community_extension_blocked(secure_mode_client):
    """Community extensions are blocked in secure mode."""
    result = await secure_mode_client.call_tool_mcp(
        "execute_query", {"sql": "INSTALL some_fake_extension FROM community"}
    )
    assert result.isError is True


@pytest.mark.asyncio
async def test_config_change_blocked(secure_mode_client):
    """Configuration changes are blocked in secure mode."""
    result = await secure_mode_client.call_tool_mcp(
        "execute_query", {"sql": "SET threads = 1"}
    )
    assert result.isError is True
    text = get_result_text(result)
    assert "lock" in text.lower() or "cannot" in text.lower()


@pytest.mark.asyncio
async def test_read_from_database_works(secure_mode_client):
    """Reading from the database still works in secure mode."""
    result = await secure_mode_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT COUNT(*) as cnt FROM users"}
    )
    assert result.isError is False
    text = get_result_text(result)
    assert "cnt" in text
