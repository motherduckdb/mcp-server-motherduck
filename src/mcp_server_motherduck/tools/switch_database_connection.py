"""
Switch database connection tool - Change the primary database connection.
"""

import os
from typing import Any

DESCRIPTION = "Switch to a different database connection. The new connection respects the server's read-only/read-write mode."


def _is_local_file_path(path: str) -> bool:
    """Check if path is a local file path (not :memory:, md:, s3://, etc.)."""
    if path == ":memory:":
        return False
    if path.startswith("md:") or path.startswith("motherduck:"):
        return False
    if path.startswith("s3://"):
        return False
    return True


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
    if not _is_local_file_path(path):
        return None

    # Local file paths must be absolute
    if not os.path.isabs(path):
        return f"Relative paths are not allowed. Please use an absolute path. Got: {path}"

    return None


def switch_database_connection(
    path: str,
    db_client: Any,
    server_read_only: bool = False,
    create_if_not_exists: bool = False,
) -> dict[str, Any]:
    """
    Switch to a different primary database.

    Args:
        path: Database path. For local files, must be an absolute path.
              Also accepts :memory:, md:database_name, or s3:// paths.
        db_client: DatabaseClient instance (injected by server)
        server_read_only: Server's global read-only setting (injected by server)
        create_if_not_exists: If True, create the database file if it doesn't exist.
                          Only allowed when server is in read-write mode.

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

    # For local file paths, check if file exists
    if _is_local_file_path(path):
        file_exists = os.path.exists(path)

        if not file_exists:
            if not create_if_not_exists:
                return {
                    "success": False,
                    "error": f"Database file does not exist: {path}. Set create_if_not_exists=True to create a new database.",
                    "errorType": "FileNotFoundError",
                }

            if server_read_only:
                return {
                    "success": False,
                    "error": "Cannot create new database file in read-only mode. The server must be started with --read-write to create databases.",
                    "errorType": "PermissionError",
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
