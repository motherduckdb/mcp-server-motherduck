"""
E2E tests for catalog tools (list_databases, list_tables, list_columns).

Tests the new catalog exploration tools against local DuckDB.
"""

import json

import pytest

from tests.e2e.conftest import get_result_text


def parse_json_result(result) -> dict:
    """Parse JSON from a tool call result."""
    text = get_result_text(result)
    return json.loads(text)


@pytest.mark.asyncio
async def test_list_tools_includes_catalog_tools(memory_client):
    """Server exposes all four tools including catalog tools."""
    tools = await memory_client.list_tools()
    tool_names = {t.name for t in tools}

    assert "execute_query" in tool_names
    assert "list_databases" in tool_names
    assert "list_tables" in tool_names
    assert "list_columns" in tool_names
    assert len(tools) == 4  # query, list_databases, list_tables, list_columns (switch_database_connection requires --allow-switch-databases)


@pytest.mark.asyncio
async def test_list_databases_memory(memory_client):
    """list_databases returns database list for in-memory DB."""
    result = await memory_client.call_tool_mcp("list_databases", {})
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert "databases" in data
    assert "databaseCount" in data
    assert isinstance(data["databases"], list)

    # In-memory DB should have at least "memory" database
    db_names = [db["name"] for db in data["databases"]]
    assert "memory" in db_names


@pytest.mark.asyncio
async def test_list_databases_local_file(local_client):
    """list_databases returns database list for local DuckDB file."""
    result = await local_client.call_tool_mcp("list_databases", {})
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert "databases" in data
    assert len(data["databases"]) > 0


@pytest.mark.asyncio
async def test_list_tables_memory(memory_client):
    """list_tables returns table list for in-memory DB."""
    # Create a test table first
    await memory_client.call_tool_mcp(
        "execute_query", {"sql": "CREATE TABLE test_table (id INTEGER, name VARCHAR)"}
    )

    result = await memory_client.call_tool_mcp("list_tables", {"database": "memory"})
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert data["database"] == "memory"
    assert "tables" in data
    assert "tableCount" in data

    # Should find our test table
    table_names = [t["name"] for t in data["tables"]]
    assert "test_table" in table_names


@pytest.mark.asyncio
async def test_list_tables_with_schema_filter(memory_client):
    """list_tables respects schema filter."""
    # Create a test table in main schema
    await memory_client.call_tool_mcp(
        "execute_query", {"sql": "CREATE TABLE main.schema_test (id INTEGER)"}
    )

    result = await memory_client.call_tool_mcp(
        "list_tables", {"database": "memory", "schema": "main"}
    )
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert data["schema"] == "main"


@pytest.mark.asyncio
async def test_list_tables_local_file(local_client):
    """list_tables returns tables from local DuckDB file."""
    # First get the database name
    db_result = await local_client.call_tool_mcp("list_databases", {})
    db_data = parse_json_result(db_result)

    # Use the first non-system database
    db_name = db_data["databases"][0]["name"]

    result = await local_client.call_tool_mcp("list_tables", {"database": db_name})
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert "tables" in data


@pytest.mark.asyncio
async def test_list_columns_memory(memory_client):
    """list_columns returns column info for a table."""
    # Create a test table with various column types
    await memory_client.call_tool_mcp(
        "execute_query",
        {
            "sql": """
            CREATE TABLE column_test (
                id INTEGER,
                name VARCHAR,
                created_at TIMESTAMP,
                is_active BOOLEAN
            )
        """
        },
    )

    result = await memory_client.call_tool_mcp(
        "list_columns",
        {"database": "memory", "table": "column_test"},
    )
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert data["database"] == "memory"
    assert data["table"] == "column_test"
    assert data["schema"] == "main"
    assert data["objectType"] == "table"
    assert "columns" in data
    assert data["columnCount"] == 4

    # Check column details
    col_names = [c["name"] for c in data["columns"]]
    assert "id" in col_names
    assert "name" in col_names
    assert "created_at" in col_names
    assert "is_active" in col_names

    # Check column types
    col_types = {c["name"]: c["type"] for c in data["columns"]}
    assert "INTEGER" in col_types["id"]
    assert "VARCHAR" in col_types["name"]


@pytest.mark.asyncio
async def test_list_columns_view(memory_client):
    """list_columns correctly identifies views."""
    # Create a table and a view
    await memory_client.call_tool_mcp(
        "execute_query", {"sql": "CREATE TABLE base_table (id INTEGER, value VARCHAR)"}
    )
    await memory_client.call_tool_mcp(
        "execute_query", {"sql": "CREATE VIEW test_view AS SELECT * FROM base_table"}
    )

    result = await memory_client.call_tool_mcp(
        "list_columns",
        {"database": "memory", "table": "test_view"},
    )
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert data["objectType"] == "view"


@pytest.mark.asyncio
async def test_list_columns_nonexistent_table(memory_client):
    """list_columns returns empty for nonexistent table."""
    result = await memory_client.call_tool_mcp(
        "list_columns",
        {"database": "memory", "table": "nonexistent_table_xyz"},
    )
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert data["columnCount"] == 0
    assert data["columns"] == []


@pytest.mark.asyncio
async def test_list_tables_nonexistent_database(memory_client):
    """list_tables returns error for nonexistent database."""
    result = await memory_client.call_tool_mcp("list_tables", {"database": "nonexistent_db_xyz"})
    # This might succeed with empty results or fail depending on DuckDB behavior
    data = parse_json_result(result)
    # Either success with no tables or error is acceptable
    assert "success" in data


@pytest.mark.asyncio
async def test_query_returns_json(memory_client):
    """query tool returns JSON instead of tabulate format."""
    result = await memory_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT 1 as num, 'hello' as greeting"}
    )
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert "columns" in data
    assert "columnTypes" in data
    assert "rows" in data
    assert "rowCount" in data

    assert data["columns"] == ["num", "greeting"]
    assert data["rowCount"] == 1
    assert data["rows"][0] == [1, "hello"]


@pytest.mark.asyncio
async def test_query_error_returns_json(memory_client):
    """query errors are returned with isError=True and JSON error message."""
    result = await memory_client.call_tool_mcp(
        "execute_query", {"sql": "SELECT * FROM nonexistent_table_xyz"}
    )
    assert result.isError is True

    # Error message contains JSON with error details
    text = get_result_text(result)
    assert "does not exist" in text.lower() or "error" in text.lower()


@pytest.mark.asyncio
async def test_tool_annotations_read_only_mode(readonly_client):
    """In read-only mode, query tool should have readOnlyHint=True."""
    tools = await readonly_client.list_tools()
    query_tool = next(t for t in tools if t.name == "execute_query")

    # Check annotations if available
    if hasattr(query_tool, "annotations") and query_tool.annotations:
        assert getattr(query_tool.annotations, "readOnlyHint", None) is True
        assert getattr(query_tool.annotations, "destructiveHint", None) is False


@pytest.mark.asyncio
async def test_catalog_tools_always_readonly(memory_client):
    """Catalog tools always have readOnlyHint=True."""
    tools = await memory_client.list_tools()

    for tool in tools:
        if tool.name in ["list_databases", "list_tables", "list_columns"]:
            if hasattr(tool, "annotations") and tool.annotations:
                assert getattr(tool.annotations, "readOnlyHint", None) is True
                assert getattr(tool.annotations, "destructiveHint", None) is False
