"""
List tables tool - List all tables and views in a database.
"""

from typing import Any

DESCRIPTION = (
    "List all tables and views in a database with their comments. "
    "If database is not specified, uses the current database."
)


def list_tables(
    db_client: Any,
    database: str | None = None,
    schema: str | None = None,
) -> dict[str, Any]:
    """
    List all tables and views in a database.

    Args:
        db_client: DatabaseClient instance (injected by server)
        database: Database name to list tables from (defaults to current database)
        schema: Optional schema name to filter by (defaults to all schemas)

    Returns:
        JSON-serializable dict with table/view list or error
    """
    try:
        # Get current database if not specified
        if database is None:
            _, _, db_rows = db_client.execute_raw("SELECT current_database()")
            database = db_rows[0][0]

        # Build schema filter
        schema_filter = f"AND schema_name = '{schema}'" if schema else ""

        # Query tables and views using DuckDB system functions
        sql = f"""
            SELECT
                schema_name as schema,
                table_name as name,
                'table' as type,
                comment
            FROM duckdb_tables()
            WHERE database_name = '{database}' {schema_filter}

            UNION ALL

            SELECT
                schema_name as schema,
                view_name as name,
                'view' as type,
                comment
            FROM duckdb_views()
            WHERE database_name = '{database}' {schema_filter}

            ORDER BY schema, type, name
        """

        _, _, rows = db_client.execute_raw(sql)

        # Transform results
        tables = [
            {
                "schema": row[0],
                "name": row[1],
                "type": row[2],
                "comment": row[3] if row[3] else None,
            }
            for row in rows
        ]

        table_count = sum(1 for t in tables if t["type"] == "table")
        view_count = sum(1 for t in tables if t["type"] == "view")

        return {
            "success": True,
            "database": database,
            "schema": schema or "all",
            "tables": tables,
            "tableCount": table_count,
            "viewCount": view_count,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__,
        }
