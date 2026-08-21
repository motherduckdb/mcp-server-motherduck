"""
List tables tool - List all tables and views in a database.
"""

from typing import Any

from ..database import quote_sql_string

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

        # Validate explicit catalog filters so an unknown database or schema is
        # distinguishable from an existing catalog that contains no objects.
        _, _, database_rows = db_client.execute_raw(f"""
            SELECT 1
            FROM duckdb_databases()
            WHERE database_name = {quote_sql_string(database)}
            LIMIT 1
        """)
        if not database_rows:
            return {
                "success": False,
                "database": database,
                "schema": schema or "all",
                "error": f"Database not found: {database}",
                "errorType": "NotFoundError",
            }

        if schema is not None:
            _, _, schema_rows = db_client.execute_raw(f"""
                SELECT 1
                FROM duckdb_schemas()
                WHERE database_name = {quote_sql_string(database)}
                  AND schema_name = {quote_sql_string(schema)}
                LIMIT 1
            """)
            if not schema_rows:
                return {
                    "success": False,
                    "database": database,
                    "schema": schema,
                    "error": f"Schema not found: {database}.{schema}",
                    "errorType": "NotFoundError",
                }

        # Build schema filter
        schema_filter = f"AND schema_name = {quote_sql_string(schema)}" if schema else ""

        # Query tables and views using DuckDB system functions
        db_quoted = quote_sql_string(database)
        sql = f"""
            SELECT
                schema_name as schema,
                table_name as name,
                'table' as type,
                comment
            FROM duckdb_tables()
            WHERE database_name = {db_quoted} {schema_filter}

            UNION ALL

            SELECT
                schema_name as schema,
                view_name as name,
                'view' as type,
                comment
            FROM duckdb_views()
            WHERE database_name = {db_quoted} {schema_filter}

            ORDER BY schema, type, name
        """

        _, _, rows = db_client.execute_raw(sql)

        # Transform results — names are pre-quoted when they need it
        tables = [
            {
                "schema": row[0],
                "name": db_client.quote_identifier_for_display(row[1]),
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
