"""
MCP Tools for MotherDuck/DuckDB server.

Each tool is defined in its own module and exported here.
"""

from .list_columns import list_columns
from .list_databases import list_databases
from .list_tables import list_tables
from .query import query
from .switch_database_connection import switch_database_connection

__all__ = [
    "query",
    "list_databases",
    "list_tables",
    "list_columns",
    "switch_database_connection",
]
