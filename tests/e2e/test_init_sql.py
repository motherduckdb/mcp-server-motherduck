"""
E2E tests for --init-sql feature.

Tests database initialization SQL execution on startup.
"""

import json

import pytest
from fastmcp import Client


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
def init_sql_string():
    """Simple init SQL string."""
    return "CREATE TABLE init_test (id INTEGER, name VARCHAR); INSERT INTO init_test VALUES (1, 'from_init');"


@pytest.fixture
def init_sql_file(tmp_path):
    """Create a temporary SQL file for init."""
    sql_file = tmp_path / "init.sql"
    sql_file.write_text(
        "CREATE TABLE file_init_test (id INTEGER, value VARCHAR);\n"
        "INSERT INTO file_init_test VALUES (1, 'from_file'), (2, 'also_from_file');"
    )
    return str(sql_file)


@pytest.fixture
async def init_sql_string_client(init_sql_string):
    """Client with init SQL string."""
    from mcp_server_motherduck.server import create_mcp_server

    mcp = create_mcp_server(
        db_path=":memory:",
        init_sql=init_sql_string,
    )
    async with Client(mcp) as client:
        yield client


@pytest.fixture
async def init_sql_file_client(init_sql_file):
    """Client with init SQL file."""
    from mcp_server_motherduck.server import create_mcp_server

    mcp = create_mcp_server(
        db_path=":memory:",
        init_sql=init_sql_file,
    )
    async with Client(mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_init_sql_string_creates_table(init_sql_string_client):
    """Init SQL string creates table on startup."""
    result = await init_sql_string_client.call_tool_mcp("query", {"sql": "SELECT * FROM init_test"})
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert data["rowCount"] == 1
    assert data["rows"][0][1] == "from_init"


@pytest.mark.asyncio
async def test_init_sql_file_creates_table(init_sql_file_client):
    """Init SQL file creates table on startup."""
    result = await init_sql_file_client.call_tool_mcp(
        "query", {"sql": "SELECT * FROM file_init_test ORDER BY id"}
    )
    assert result.isError is False

    data = parse_json_result(result)
    assert data["success"] is True
    assert data["rowCount"] == 2
    assert data["rows"][0][1] == "from_file"
    assert data["rows"][1][1] == "also_from_file"


@pytest.mark.asyncio
async def test_init_sql_with_multiple_statements():
    """Init SQL can contain multiple statements."""
    from mcp_server_motherduck.server import create_mcp_server

    init_sql = """
    CREATE TABLE users (id INTEGER, name VARCHAR);
    CREATE TABLE orders (id INTEGER, user_id INTEGER, total DECIMAL);
    INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob');
    INSERT INTO orders VALUES (1, 1, 99.99), (2, 1, 49.99), (3, 2, 75.00);
    """

    mcp = create_mcp_server(db_path=":memory:", init_sql=init_sql)
    async with Client(mcp) as client:
        # Check users table
        result = await client.call_tool_mcp("query", {"sql": "SELECT COUNT(*) as cnt FROM users"})
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["rows"][0][0] == 2

        # Check orders table
        result = await client.call_tool_mcp("query", {"sql": "SELECT COUNT(*) as cnt FROM orders"})
        data = parse_json_result(result)
        assert data["success"] is True
        assert data["rows"][0][0] == 3


@pytest.mark.asyncio
async def test_init_sql_none_works():
    """Server works fine without init SQL."""
    from mcp_server_motherduck.server import create_mcp_server

    mcp = create_mcp_server(db_path=":memory:", init_sql=None)
    async with Client(mcp) as client:
        result = await client.call_tool_mcp("query", {"sql": "SELECT 1 as num"})
        assert result.isError is False


@pytest.mark.asyncio
async def test_init_sql_error_raises():
    """Invalid init SQL raises error on startup."""
    from mcp_server_motherduck.server import create_mcp_server

    with pytest.raises(ValueError, match="Init SQL execution failed"):
        create_mcp_server(
            db_path=":memory:",
            init_sql="THIS IS NOT VALID SQL SYNTAX!!!",
        )


@pytest.mark.asyncio
async def test_init_sql_nonexistent_file():
    """Non-existent file path is treated as SQL string (and will fail)."""
    from mcp_server_motherduck.server import create_mcp_server

    # A path that doesn't exist will be treated as SQL string
    # and will fail because it's not valid SQL
    with pytest.raises(ValueError, match="Init SQL execution failed"):
        create_mcp_server(
            db_path=":memory:",
            init_sql="/nonexistent/path/to/file.sql",
        )
