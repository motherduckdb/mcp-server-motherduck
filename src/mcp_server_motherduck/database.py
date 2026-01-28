import json
import logging
import os
import re
import threading
from typing import Any, Literal, Optional

import duckdb

from .configs import SERVER_VERSION

logger = logging.getLogger("mcp_server_motherduck")


def _is_read_scaling_connection(conn: duckdb.DuckDBPyConnection) -> bool:
    """
    Check if a MotherDuck connection is using read-scaling.

    Read-scaling connections have a duckling ID ending with .rs.{number}
    e.g., "omni_primary.rs.3", "mcp_server.rs.0"

    Read-write connections end with .rw
    e.g., "omni_primary.rw", "mcp_server.rw"
    """
    try:
        # __md_duckling_id() is a table function, must use FROM clause
        result = conn.execute("SELECT * FROM __md_duckling_id()").fetchone()
        if result and result[0]:
            duckling_id = result[0]
            # Check if duckling ID ends with .rs.{number}
            return bool(re.search(r"\.rs\.\d+$", duckling_id))
        return False
    except Exception:
        return False


class DatabaseClient:
    def __init__(
        self,
        db_path: str | None = None,
        motherduck_token: str | None = None,
        home_dir: str | None = None,
        saas_mode: bool = False,
        read_only: bool = False,
        ephemeral_connections: bool = True,
        max_rows: int = 1024,
        max_chars: int = 50000,
        query_timeout: int = -1,
        init_sql: str | None = None,
        secure_mode: bool = False,
    ):
        self._read_only = read_only
        self._ephemeral_connections = ephemeral_connections
        self._max_rows = max_rows
        self._max_chars = max_chars
        self._query_timeout = query_timeout
        self._init_sql = init_sql
        self._secure_mode = secure_mode
        self.db_path, self.db_type = self._resolve_db_path_type(
            db_path, motherduck_token, saas_mode
        )
        logger.info(f"Database client initialized in `{self.db_type}` mode")

        # Set the home directory for DuckDB
        if home_dir:
            os.environ["HOME"] = home_dir

        self.conn = self._initialize_connection()

    def _initialize_connection(self) -> Optional[duckdb.DuckDBPyConnection]:
        """Initialize connection to the MotherDuck or DuckDB database"""

        logger.info(f"🔌 Connecting to {self.db_type} database")

        # Read-only handling for local DuckDB files (not in-memory)
        is_local_file = self.db_type == "duckdb" and self.db_path != ":memory:"

        if is_local_file and self._read_only:
            # For read-only local DuckDB files, use short-lived connections by default
            # to allow concurrent access from other processes
            try:
                conn = duckdb.connect(
                    self.db_path,
                    config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
                    read_only=self._read_only,
                )
                conn.execute("SELECT 1")

                if self._ephemeral_connections:
                    # Default: close connection for concurrent access
                    conn.close()
                    return None
                else:
                    # User requested persistent connection via --no-ephemeral-connections
                    logger.info("Using persistent read-only connection")
                    # Apply security settings and init SQL
                    self._apply_security_settings(conn)
                    self._execute_init_sql(conn)
                    return conn
            except Exception as e:
                logger.error(f"❌ Read-only check failed: {e}")
                raise

        # Check if this is an S3 path
        if self.db_type == "s3":
            # For S3, we need to create an in-memory connection and attach the S3 database
            conn = duckdb.connect(":memory:")

            # Install and load the httpfs extension for S3 support
            import io
            from contextlib import redirect_stderr, redirect_stdout

            null_file = io.StringIO()
            with redirect_stdout(null_file), redirect_stderr(null_file):
                try:
                    conn.execute("INSTALL httpfs;")
                except Exception:
                    pass  # Extension might already be installed
                conn.execute("LOAD httpfs;")

            # Configure S3 credentials from environment variables using CREATE SECRET
            aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
            aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
            aws_session_token = os.environ.get("AWS_SESSION_TOKEN")
            aws_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

            if aws_access_key and aws_secret_key and not aws_session_token:
                # Use CREATE SECRET for better credential management
                conn.execute(f"""
                    CREATE SECRET IF NOT EXISTS s3_secret (
                        TYPE S3,
                        KEY_ID '{aws_access_key}',
                        SECRET '{aws_secret_key}',
                        REGION '{aws_region}'
                    );
                """)
            elif aws_session_token:
                # Use credential_chain provider to automatically fetch credentials
                # This supports IAM roles, SSO, instance profiles, etc.
                conn.execute(f"""
                    CREATE SECRET IF NOT EXISTS s3_secret (
                        TYPE S3,
                        PROVIDER credential_chain,
                        REGION '{aws_region}'
                    );
                """)

            # Attach the S3 database
            try:
                # For S3, we always attach as READ_ONLY since S3 storage is typically read-only
                # Even when not in read_only mode, we attach as READ_ONLY for S3
                conn.execute(f"ATTACH '{self.db_path}' AS s3db (READ_ONLY);")
                # Use the attached database
                conn.execute("USE s3db;")
                logger.info(
                    f"✅ Successfully connected to {self.db_type} database (attached as read-only)"
                )
            except Exception as e:
                logger.error(f"Failed to attach S3 database: {e}")
                # If the database doesn't exist and we're not in read-only mode, try to create it
                if "database does not exist" in str(e) and not self._read_only:
                    logger.info("S3 database doesn't exist, attempting to create it...")
                    try:
                        # Create a new database at the S3 location
                        conn.execute(f"ATTACH '{self.db_path}' AS s3db;")
                        conn.execute("USE s3db;")
                        logger.info(f"✅ Created new S3 database at {self.db_path}")
                    except Exception as create_error:
                        logger.error(f"Failed to create S3 database: {create_error}")
                        raise
                else:
                    raise

            # Apply security settings and init SQL
            self._apply_security_settings(conn)
            self._execute_init_sql(conn)
            return conn

        # For MotherDuck, pass read_only flag; for in-memory it's not applicable
        read_only_flag = self._read_only if self.db_type == "motherduck" else False

        conn = duckdb.connect(
            self.db_path,
            config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
            read_only=read_only_flag,
        )

        logger.info(f"✅ Successfully connected to {self.db_type} database")

        # For MotherDuck with --read-only flag, verify it's a read-scaling connection
        if self.db_type == "motherduck" and self._read_only:
            if not _is_read_scaling_connection(conn):
                conn.close()
                raise ValueError(
                    "The --read-only flag with MotherDuck requires a read-scaling token. "
                    "You appear to be using a read/write token. Please use a read-scaling token instead. "
                    "See: https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/"
                )
            logger.info("Verified read-scaling connection for --read-only mode")

        # Apply security settings and init SQL
        self._apply_security_settings(conn)
        self._execute_init_sql(conn)

        return conn

    def _apply_security_settings(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Apply security settings to the connection."""
        if self._secure_mode:
            # Disable local filesystem access
            conn.execute("SET disabled_filesystems = 'LocalFileSystem'")
            # Disable community extensions (only allow core extensions)
            conn.execute("SET allow_community_extensions = false")
            # Disable auto-installing extensions
            conn.execute("SET autoinstall_known_extensions = false")
            # Lock configuration to prevent changes
            conn.execute("SET lock_configuration = true")
            logger.info("Applied secure mode settings")

    def _execute_init_sql(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Execute initialization SQL if provided."""
        if not self._init_sql:
            return

        try:
            # Check if init_sql is a file path
            if os.path.isfile(self._init_sql):
                logger.info(f"Loading init SQL from file: {self._init_sql}")
                with open(self._init_sql) as f:
                    sql_content = f.read()
            else:
                # Treat as raw SQL string
                logger.info("Executing init SQL string")
                sql_content = self._init_sql

            # Execute the SQL
            conn.execute(sql_content)
            logger.info("Init SQL executed successfully")

        except Exception as e:
            logger.error(f"Failed to execute init SQL: {e}")
            raise ValueError(f"Init SQL execution failed: {e}") from e

    def _resolve_db_path_type(
        self, db_path: str, motherduck_token: str | None = None, saas_mode: bool = False
    ) -> tuple[str, Literal["duckdb", "motherduck", "s3"]]:
        """Resolve and validate the database path"""
        # Handle S3 paths
        if db_path.startswith("s3://"):
            return db_path, "s3"

        # Handle MotherDuck paths
        if db_path.startswith("md:"):
            if motherduck_token:
                logger.info("Using MotherDuck token to connect to database `md:`")
                if saas_mode:
                    logger.info("Connecting to MotherDuck in SaaS mode")
                    return (
                        f"{db_path}?motherduck_token={motherduck_token}&saas_mode=true",
                        "motherduck",
                    )
                else:
                    return (
                        f"{db_path}?motherduck_token={motherduck_token}",
                        "motherduck",
                    )
            elif os.getenv("motherduck_token"):
                logger.info("Using MotherDuck token from env to connect to database `md:`")
                return (
                    f"{db_path}?motherduck_token={os.getenv('motherduck_token')}",
                    "motherduck",
                )
            else:
                raise ValueError(
                    "Please set the `motherduck_token` as an environment variable or pass it as an argument with `--motherduck-token` when using `md:` as db_path."
                )

        if db_path == ":memory:":
            return db_path, "duckdb"

        return db_path, "duckdb"

    def _execute(self, query: str) -> dict[str, Any]:
        """Execute query and return JSON-serializable result."""
        # Get connection to use
        if self.conn is None:
            conn = duckdb.connect(
                self.db_path,
                config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
                read_only=self._read_only,
            )
            # Apply security settings to ephemeral connection
            self._apply_security_settings(conn)
        else:
            conn = self.conn

        try:
            # Execute with or without timeout
            if self._query_timeout > 0:
                columns, column_types, rows, has_more_rows = self._execute_with_timeout(conn, query)
            else:
                columns, column_types, rows, has_more_rows = self._execute_direct(conn, query)

            # Build result object
            result: dict[str, Any] = {
                "success": True,
                "columns": columns,
                "columnTypes": column_types,
                "rows": rows,
                "rowCount": len(rows),
            }

            # Add row truncation warning
            if has_more_rows:
                result["truncated"] = True
                result["warning"] = (
                    f"Results limited to {self._max_rows:,} rows. " "Query returned more data."
                )

            # Check character limit on JSON output
            json_output = json.dumps(result, default=str)
            if len(json_output) > self._max_chars:
                # Progressively reduce rows until under limit
                while rows and len(json_output) > self._max_chars:
                    # Remove ~10% of rows each iteration
                    remove_count = max(1, len(rows) // 10)
                    rows = rows[:-remove_count]
                    result["rows"] = rows
                    result["rowCount"] = len(rows)
                    result["truncated"] = True
                    result["warning"] = (
                        f"Results limited to {len(rows):,} rows due to "
                        f"{self._max_chars // 1000}KB output size limit."
                    )
                    json_output = json.dumps(result, default=str)

            return result

        finally:
            # Close connection if it was temporary
            if self.conn is None:
                conn.close()

    def _execute_direct(
        self, conn: duckdb.DuckDBPyConnection, query: str
    ) -> tuple[list[str], list[str], list[list[Any]], bool]:
        """Execute query without timeout - returns columns, types, rows, has_more."""
        q = conn.execute(query)

        # Get column metadata
        columns = [d[0] for d in q.description] if q.description else []
        column_types = [str(d[1]) for d in q.description] if q.description else []

        # Fetch rows (max_rows + 1 to detect truncation)
        raw_rows = q.fetchmany(self._max_rows + 1)
        has_more_rows = len(raw_rows) > self._max_rows
        if has_more_rows:
            raw_rows = raw_rows[: self._max_rows]

        # Convert rows to JSON-serializable lists
        rows = [list(row) for row in raw_rows]

        return columns, column_types, rows, has_more_rows

    def _execute_with_timeout(
        self, conn: duckdb.DuckDBPyConnection, query: str
    ) -> tuple[list[str], list[str], list[list[Any]], bool]:
        """Execute query with timeout using threading.Timer and conn.interrupt()."""
        timer = threading.Timer(self._query_timeout, conn.interrupt)
        timer.start()

        try:
            return self._execute_direct(conn, query)
        except duckdb.InterruptException:
            raise ValueError(
                f"Query execution timed out after {self._query_timeout} seconds. "
                "Increase timeout with --query-timeout argument when starting the mcp server."
            )
        finally:
            timer.cancel()

    def query(self, query: str) -> dict[str, Any]:
        """Execute a SQL query and return JSON-serializable result."""
        try:
            return self._execute(query)
        except ValueError:
            # Re-raise ValueError (timeout, etc.) as-is
            raise
        except Exception as e:
            # Return error as structured response
            return {
                "success": False,
                "error": str(e),
                "errorType": type(e).__name__,
            }

    def execute_raw(self, query: str) -> tuple[list[str], list[str], list[list[Any]]]:
        """
        Execute a query and return raw results (columns, types, rows).
        Used by catalog tools that need custom result formatting.
        """
        if self.conn is None:
            conn = duckdb.connect(
                self.db_path,
                config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
                read_only=self._read_only,
            )
            # Apply security settings to ephemeral connection
            self._apply_security_settings(conn)
        else:
            conn = self.conn

        try:
            q = conn.execute(query)
            columns = [d[0] for d in q.description] if q.description else []
            column_types = [str(d[1]) for d in q.description] if q.description else []
            rows = [list(row) for row in q.fetchall()]
            return columns, column_types, rows
        finally:
            if self.conn is None:
                conn.close()

    def switch_database(self, path: str, read_only: bool = True) -> None:
        """
        Switch to a different primary database.

        Closes any existing connection and updates the database path.
        The next query will connect to the new database.

        Args:
            path: New database path (local file, :memory:, or md:database_name)
            read_only: Whether to connect in read-only mode
        """
        # Close existing connection if any
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass  # Ignore close errors
            self.conn = None

        # Update database configuration
        self.db_path = path
        self._read_only = read_only

        # Determine new database type
        if path.startswith("md:") or path.startswith("motherduck:"):
            self.db_type = "motherduck"
        elif path.startswith("s3://"):
            self.db_type = "s3"
        elif path == ":memory:":
            self.db_type = "memory"
        else:
            self.db_type = "duckdb"

        # Re-initialize connection (will be None for read-only local DuckDB)
        self.conn = self._initialize_connection()

        logger.info(f"Switched to database: {path} (read_only={read_only})")
