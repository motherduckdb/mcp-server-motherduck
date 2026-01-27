"""
Server instructions for DuckDB/MotherDuck MCP Server.

These instructions are sent to the client during initialization
to provide context about how to use the server's capabilities.
"""

INSTRUCTIONS = """Execute SQL queries against DuckDB and MotherDuck databases using DuckDB SQL syntax.

## Available Tools

- `query`: Execute SQL queries (DuckDB SQL dialect)
- `list_databases`: List all available databases
- `list_tables`: List tables and views in a database
- `list_columns`: List columns of a table or view

## DuckDB SQL Quick Reference

**Name Qualification**
- Format: `database.schema.table` or just `schema.table` or `table`
- Default schema is `main`: `db.table` = `db.main.table`
- Use fully qualified names when joining tables across different databases

**Identifiers and Literals:**
- Use double quotes (`"`) for identifiers with spaces/special characters or case-sensitivity
- Use single quotes (`'`) for string literals

**Flexible Query Structure:**
- Queries can start with `FROM`: `FROM my_table WHERE condition;`
- `SELECT` without `FROM` for expressions: `SELECT 1 + 1 AS result;`
- Support for `CREATE TABLE AS` (CTAS): `CREATE TABLE new_table AS SELECT * FROM old_table;`

**Advanced Column Selection:**
- Exclude columns: `SELECT * EXCLUDE (sensitive_data) FROM users;`
- Replace columns: `SELECT * REPLACE (UPPER(name) AS name) FROM users;`
- Pattern matching: `SELECT COLUMNS('sales_.*') FROM sales_data;`

**Grouping and Ordering Shortcuts:**
- Group by all non-aggregated columns: `SELECT category, SUM(sales) FROM sales_data GROUP BY ALL;`
- Order by all columns: `SELECT * FROM my_table ORDER BY ALL;`

**Complex Data Types:**
- Lists: `SELECT [1, 2, 3] AS my_list;`
- Structs: `SELECT {'a': 1, 'b': 'text'} AS my_struct;`
- Maps: `SELECT MAP([1,2],['one','two']) AS my_map;`
- JSON: `json_col->>'key'` (returns text) or `data->'$.user.id'` (returns JSON)

**Date/Time Operations:**
- String to timestamp: `strptime('2023-07-23', '%Y-%m-%d')::TIMESTAMP`
- Format timestamp: `strftime(NOW(), '%Y-%m-%d')`
- Extract parts: `EXTRACT(YEAR FROM DATE '2023-07-23')`

### Schema Exploration

```sql
-- List all databases
SELECT database_name, type FROM duckdb_databases();

-- For MotherDuck: List all databases (including shared)
SELECT alias as database_name, type FROM MD_ALL_DATABASES();

-- List tables in a database
SELECT schema_name, table_name FROM duckdb_tables()
WHERE database_name = 'your_db';

-- Get column info
SELECT column_name, data_type FROM duckdb_columns()
WHERE database_name = 'your_db' AND table_name = 'your_table';

-- Quick preview with statistics
SUMMARIZE your_table;
```

### Query Best Practices

- Filter early to reduce data volume before blocking operations
- Use CTEs to break complex queries into manageable parts
- Avoid unnecessary `ORDER BY` on intermediate results
- Use `arg_max()` and `arg_min()` for "most recent" queries
- Use `QUALIFY` for filtering window function results

```sql
-- Get top 2 products by sales in each category
SELECT category, product_name, sales_amount
FROM products
QUALIFY ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales_amount DESC) <= 2;
```
"""


def get_instructions(read_only: bool = False, saas_mode: bool = False) -> str:
    """
    Get server instructions with connection context.

    Args:
        read_only: Whether the server is in read-only mode
        saas_mode: Whether MotherDuck is in SaaS mode

    Returns:
        Instructions string with context header
    """
    context_lines = []

    if read_only:
        context_lines.append("- **Read-only mode**: Write operations are disabled")

    if saas_mode:
        context_lines.append(
            "- **SaaS mode**: Local filesystem access is restricted"
        )

    if context_lines:
        context = "## Connection Context\n\n" + "\n".join(context_lines) + "\n\n"
        return context + INSTRUCTIONS

    return INSTRUCTIONS
