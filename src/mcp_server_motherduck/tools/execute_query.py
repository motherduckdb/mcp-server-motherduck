"""
Execute Query tool - Execute SQL queries against DuckDB/MotherDuck databases.
"""

from typing import Any

DESCRIPTION = "Execute a SQL query on the DuckDB or MotherDuck database."


def execute_query(sql: str, db_client: Any) -> dict[str, Any]:
    """
    Execute a SQL query on the DuckDB or MotherDuck database.

    Args:
        sql: SQL query to execute (DuckDB SQL dialect)
        db_client: DatabaseClient instance (injected by server)

    Returns:
        JSON-serializable dict with query results or error
    """
    return db_client.query(sql)
