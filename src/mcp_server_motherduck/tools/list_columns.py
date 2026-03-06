"""
List columns tool - List all columns of a table or view.
"""

from typing import Any

from psycopg2.extensions import adapt

DESCRIPTION = (
    "List all columns of a table or view with their types and comments. "
    "If database/schema are not specified, uses the current database/schema."
)


def list_columns(
    table: str,
    db_client: Any,
    database: str | None = None,
    schema: str | None = None,
) -> dict[str, Any]:
    """
    List all columns of a table or view.

    Args:
        table: Table or view name
        db_client: DatabaseClient instance (injected by server)
        database: Database name (defaults to current database)
        schema: Schema name (defaults to current schema)

    Returns:
        JSON-serializable dict with column list or error
    """
    try:
        # Get current database if not specified
        if database is None:
            _, _, db_rows = db_client.execute_raw("SELECT current_database()")
            database = db_rows[0][0]

        # Get current schema if not specified
        if schema is None:
            _, _, schema_rows = db_client.execute_raw("SELECT current_schema()")
            schema = schema_rows[0][0]

        # Quote identifiers as SQL string literals
        db_q = adapt(database).getquoted().decode()
        schema_q = adapt(schema).getquoted().decode()
        table_q = adapt(table).getquoted().decode()

        # Query columns using DuckDB system function
        sql = f"""
            SELECT
                column_name as name,
                data_type as type,
                is_nullable = 'YES' as nullable,
                comment
            FROM duckdb_columns()
            WHERE database_name = {db_q}
              AND schema_name = {schema_q}
              AND table_name = {table_q}
            ORDER BY column_index
        """

        _, _, rows = db_client.execute_raw(sql)

        # Transform results
        columns = [
            {
                "name": row[0],
                "type": row[1],
                "nullable": bool(row[2]),
                "comment": row[3] if row[3] else None,
            }
            for row in rows
        ]

        # Determine if it's a view or table
        object_type = "table"
        try:
            _, _, view_rows = db_client.execute_raw(f"""
                SELECT 1 FROM duckdb_views()
                WHERE database_name = {db_q}
                  AND schema_name = {schema_q}
                  AND view_name = {table_q}
                LIMIT 1
            """)
            if view_rows:
                object_type = "view"
        except Exception:
            pass  # Assume table if check fails

        return {
            "success": True,
            "database": database,
            "schema": schema,
            "table": table,
            "objectType": object_type,
            "columns": columns,
            "columnCount": len(columns),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__,
        }
