"""
List databases tool - Show all databases available in the connection.
"""

from typing import Any

DESCRIPTION = "List all databases with their names and types."


def list_databases(db_client: Any) -> dict[str, Any]:
    """
    List all databases available in the connection.

    For MotherDuck: Uses MD_ALL_DATABASES() to list all databases.
    For local DuckDB: Uses duckdb_databases() system function.

    Excludes internal databases: 'system' and 'temp'.

    Args:
        db_client: DatabaseClient instance (injected by server)

    Returns:
        JSON-serializable dict with database list or error
    """
    try:
        # Try MotherDuck function first (works for MotherDuck connections)
        try:
            _, _, rows = db_client.execute_raw(
                "SELECT alias, type FROM MD_ALL_DATABASES() "
                "WHERE alias IS NOT NULL AND alias NOT IN ('system', 'temp')"
            )
            databases = [{"name": row[0], "type": row[1]} for row in rows]
        except Exception:
            # Fall back to DuckDB system function (works for local DuckDB)
            _, _, rows = db_client.execute_raw(
                "SELECT database_name, type FROM duckdb_databases() "
                "WHERE database_name NOT IN ('system', 'temp')"
            )
            databases = [{"name": row[0], "type": row[1]} for row in rows]

        return {
            "success": True,
            "databases": databases,
            "databaseCount": len(databases),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__,
        }
