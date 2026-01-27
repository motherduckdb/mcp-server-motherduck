"""
Switch database connection tool - Change the primary database connection.
"""

import os
from typing import Any

DESCRIPTION = "Switch to a different database connection. The new connection respects the server's read-only/read-write mode."


def _validate_path(path: str) -> str | None:
    """
    Validate database path.
    
    Returns None if valid, or an error message if invalid.
    
    Valid paths:
    - :memory:
    - md: or motherduck: paths
    - s3:// paths
    - Absolute local file paths
    
    Invalid:
    - Relative paths (must use absolute paths for local files)
    """
    # Special paths that are always valid
    if path == ":memory:":
        return None
    if path.startswith("md:") or path.startswith("motherduck:"):
        return None
    if path.startswith("s3://"):
        return None
    
    # Local file paths must be absolute
    if not os.path.isabs(path):
        return f"Relative paths are not allowed. Please use an absolute path. Got: {path}"
    
    return None


def switch_database_connection(
    path: str,
    db_client: Any,
    server_read_only: bool = False,
) -> dict[str, Any]:
    """
    Switch to a different primary database.

    Args:
        path: Database path. For local files, must be an absolute path.
              Also accepts :memory:, md:database_name, or s3:// paths.
        db_client: DatabaseClient instance (injected by server)
        server_read_only: Server's global read-only setting (injected by server)

    Returns:
        JSON-serializable dict with result
    """
    # Validate path
    error = _validate_path(path)
    if error:
        return {
            "success": False,
            "error": error,
            "errorType": "ValueError",
        }
    
    # In-memory databases can't be read-only (DuckDB limitation)
    if path == ":memory:":
        effective_read_only = False
        warning = (
            "In-memory databases cannot be read-only (DuckDB limitation)"
            if server_read_only
            else None
        )
    else:
        effective_read_only = server_read_only
        warning = None

    try:
        previous_db = db_client.db_path
        db_client.switch_database(path, effective_read_only)

        result: dict[str, Any] = {
            "success": True,
            "message": f"Switched to database: {path}",
            "previousDatabase": previous_db,
            "currentDatabase": path,
            "readOnly": effective_read_only,
        }

        if warning:
            result["warning"] = warning

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "errorType": type(e).__name__,
        }
