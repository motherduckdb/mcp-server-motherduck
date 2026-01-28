"""
E2E tests for switch_database_connection tool.
"""

import json

import duckdb
import pytest


def get_result_text(result) -> str:
    """Extract text from a tool call result."""
    if result.content and len(result.content) > 0:
        return result.content[0].text
    return ""


def parse_json_result(result) -> dict:
    """Parse JSON from a tool call result."""
    text = get_result_text(result)
    return json.loads(text)


@pytest.fixture
def temp_duckdb_file(tmp_path):
    """Create a temporary DuckDB file with test data."""
    db_path = tmp_path / "test_switch.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE switched_table (id INTEGER, value VARCHAR)")
    conn.execute("INSERT INTO switched_table VALUES (1, 'from_switched'), (2, 'also_switched')")
    conn.close()
    return str(db_path)


@pytest.fixture
def second_duckdb_file(tmp_path):
    """Create a second temporary DuckDB file."""
    db_path = tmp_path / "second.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE second_table (id INTEGER, name VARCHAR)")
    conn.execute("INSERT INTO second_table VALUES (100, 'from_second')")
    conn.close()
    return str(db_path)


class TestSwitchDatabaseConnection:
    """Test switch_database_connection tool."""

    @pytest.mark.asyncio
    async def test_switch_database_connection_success(self, memory_client_with_switch, temp_duckdb_file):
        """Can switch to a local DuckDB file."""
        result = await memory_client_with_switch.call_tool_mcp(
            "switch_database_connection",
            {"path": temp_duckdb_file},
        )
        assert result.isError is False

        data = parse_json_result(result)
        assert data["success"] is True
        assert data["currentDatabase"] == temp_duckdb_file
        # In-memory client doesn't have --read-only, so switched connection is read-write
        assert data["readOnly"] is False

    @pytest.mark.asyncio
    async def test_switch_and_query(self, memory_client_with_switch, temp_duckdb_file):
        """Can query after switching database."""
        # Switch to the database
        switch_result = await memory_client_with_switch.call_tool_mcp(
            "switch_database_connection",
            {"path": temp_duckdb_file},
        )
        assert switch_result.isError is False

        # Query the switched database
        query_result = await memory_client_with_switch.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT * FROM switched_table ORDER BY id"},
        )
        assert query_result.isError is False

        data = parse_json_result(query_result)
        assert data["success"] is True
        assert data["rowCount"] == 2
        assert data["rows"][0][1] == "from_switched"

    @pytest.mark.asyncio
    async def test_switch_between_databases(
        self, memory_client_with_switch, temp_duckdb_file, second_duckdb_file
    ):
        """Can switch between multiple databases."""
        # Switch to first database
        await memory_client_with_switch.call_tool_mcp(
            "switch_database_connection",
            {"path": temp_duckdb_file},
        )

        # Verify first database
        result1 = await memory_client_with_switch.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT * FROM switched_table LIMIT 1"},
        )
        data1 = parse_json_result(result1)
        assert data1["rows"][0][1] == "from_switched"

        # Switch to second database
        switch_result = await memory_client_with_switch.call_tool_mcp(
            "switch_database_connection",
            {"path": second_duckdb_file},
        )
        switch_data = parse_json_result(switch_result)
        assert switch_data["previousDatabase"] == temp_duckdb_file
        assert switch_data["currentDatabase"] == second_duckdb_file

        # Verify second database
        result2 = await memory_client_with_switch.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT * FROM second_table LIMIT 1"},
        )
        data2 = parse_json_result(result2)
        assert data2["rows"][0][1] == "from_second"

        # First database table should not be accessible
        result3 = await memory_client_with_switch.call_tool_mcp(
            "execute_query",
            {"sql": "SELECT * FROM switched_table"},
        )
        assert result3.isError is True

    @pytest.mark.asyncio
    async def test_switch_to_memory(self, memory_client_with_switch, temp_duckdb_file):
        """Can switch back to in-memory database."""
        # Start with temp file
        await memory_client_with_switch.call_tool_mcp(
            "switch_database_connection",
            {"path": temp_duckdb_file},
        )

        # Switch to memory
        result = await memory_client_with_switch.call_tool_mcp(
            "switch_database_connection",
            {"path": ":memory:"},
        )
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["currentDatabase"] == ":memory:"
        # Memory databases can't be read-only
        assert data["readOnly"] is False

    @pytest.mark.asyncio
    async def test_switch_nonexistent_file(self, memory_client_with_switch):
        """Switching to nonexistent file fails gracefully."""
        result = await memory_client_with_switch.call_tool_mcp(
            "switch_database_connection",
            {"path": "/nonexistent/path/db.duckdb"},
        )
        assert result.isError is False  # Tool returns success=false

        data = parse_json_result(result)
        assert data["success"] is False


class TestSwitchDatabaseConnectionReadOnlyServer:
    """Test switch_database_connection respects server read-only mode."""

    @pytest.mark.asyncio
    async def test_server_read_only_mode(self, tmp_path):
        """Server --read-only flag is respected by switch_database_connection."""
        from fastmcp import Client

        from mcp_server_motherduck.server import create_mcp_server

        # Create test databases
        initial_db = tmp_path / "initial.duckdb"
        conn = duckdb.connect(str(initial_db))
        conn.execute("CREATE TABLE init (id INTEGER)")
        conn.close()

        target_db = tmp_path / "target.duckdb"
        conn = duckdb.connect(str(target_db))
        conn.execute("CREATE TABLE target (id INTEGER)")
        conn.close()

        # Create server in read-only mode with switch enabled
        mcp = create_mcp_server(
            db_path=str(initial_db),
            read_only=True,  # Server is read-only
            allow_switch_databases=True,
        )

        async with Client(mcp) as client:
            # Switch to another database
            result = await client.call_tool_mcp(
                "switch_database_connection",
                {"path": str(target_db)},
            )
            data = parse_json_result(result)

            # Should succeed and be read-only (respects server mode)
            assert data["success"] is True
            assert data["readOnly"] is True


class TestSwitchDatabaseConnectionToolAvailability:
    """Test switch_database_connection tool availability based on --allow-switch-databases flag."""

    @pytest.mark.asyncio
    async def test_tool_not_available_by_default(self, memory_client):
        """switch_database_connection tool is not available by default."""
        tools = await memory_client.list_tools()
        tool_names = [t.name for t in tools]
        assert "switch_database_connection" not in tool_names

    @pytest.mark.asyncio
    async def test_tool_available_with_flag(self, memory_client_with_switch):
        """switch_database_connection tool is available when --allow-switch-databases is set."""
        tools = await memory_client_with_switch.list_tools()
        tool_names = [t.name for t in tools]
        assert "switch_database_connection" in tool_names
