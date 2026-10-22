"""The character limit applies to the JSON text returned over MCP."""

import json

import pytest
from fastmcp import Client

from mcp_server_motherduck.server import create_mcp_server


@pytest.mark.parametrize("max_chars", [600, 1200, 1800])
async def test_query_text_respects_character_limit(max_chars):
    server = create_mcp_server(db_path=":memory:", read_only=False, max_chars=max_chars)
    async with Client(server) as client:
        result = await client.call_tool_mcp(
            "execute_query", {"sql": "SELECT i FROM range(100) AS t(i)"}
        )

    assert result.isError is False
    text = result.content[0].text
    data = json.loads(text)
    assert len(text) <= max_chars
    assert data["success"] is True
    assert data["truncated"] is True
    assert 0 < data["rowCount"] < 100
    assert data["rows"] == [[i] for i in range(data["rowCount"])]


async def test_query_text_below_character_limit_keeps_all_rows():
    server = create_mcp_server(db_path=":memory:", read_only=False, max_chars=5000)
    async with Client(server) as client:
        result = await client.call_tool_mcp(
            "execute_query", {"sql": "SELECT i FROM range(100) AS t(i)"}
        )

    assert result.isError is False
    data = json.loads(result.content[0].text)
    assert data["rows"] == [[i] for i in range(100)]
    assert data["rowCount"] == 100
    assert not data.get("truncated", False)
