"""
MCP Tools for MotherDuck/DuckDB server.

Each tool is defined in its own module and exported here.
"""

from .execute_query import execute_query
from .list_columns import list_columns
from .list_databases import list_databases
from .list_tables import list_tables
from .switch_database_connection import switch_database_connection

__all__ = [
    "execute_query",
    "list_databases",
    "list_tables",
    "list_columns",
    "switch_database_connection",
]
