import os
import duckdb
from typing import Literal, Optional
from tabulate import tabulate
import logging
import threading
from .configs import SERVER_VERSION

logger = logging.getLogger("mcp_server_motherduck")


class DatabaseClient:
    def __init__(
        self,
        db_path: str | None = None,
        motherduck_token: str | None = None,
        home_dir: str | None = None,
        saas_mode: bool = False,
        read_only: bool = False,
        max_rows: int = 1024,
        max_chars: int = 50000,
        query_timeout: int = -1,
    ):
        self._read_only = read_only
        self._max_rows = max_rows
        self._max_chars = max_chars
        self._query_timeout = query_timeout
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

        # S3 databases don't support read-only mode
        if self.db_type == "s3" and self._read_only:
            raise ValueError("Read-only mode is not supported for S3 databases")

        if self.db_type == "duckdb" and self._read_only:
            # check that we can connect, issue a `select 1` and then close + return None
            try:
                conn = duckdb.connect(
                    self.db_path,
                    config={
                        "custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"
                    },
                    read_only=self._read_only,
                )
                conn.execute("SELECT 1")
                conn.close()
                return None
            except Exception as e:
                logger.error(f"❌ Read-only check failed: {e}")
                raise

        # Check if this is an S3 path
        if self.db_type == "s3":
            # For S3, we need to create an in-memory connection and attach the S3 database
            conn = duckdb.connect(':memory:')
            
            # Install and load the httpfs extension for S3 support
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            null_file = io.StringIO()
            with redirect_stdout(null_file), redirect_stderr(null_file):
                try:
                    conn.execute("INSTALL httpfs;")
                except:
                    pass  # Extension might already be installed
                conn.execute("LOAD httpfs;")
            
            # Configure S3 credentials from environment variables using CREATE SECRET
            aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
            aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
            
            
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
                logger.info(f"✅ Successfully connected to {self.db_type} database (attached as read-only)")
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
                
            return conn

        conn = duckdb.connect(
            self.db_path,
            config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
            read_only=self._read_only,
        )

        logger.info(f"✅ Successfully connected to {self.db_type} database")

        return conn

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
                logger.info(
                    "Using MotherDuck token from env to connect to database `md:`"
                )
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

    def _execute(self, query: str) -> str:
        # Get connection to use
        if self.conn is None:
            conn = duckdb.connect(
                self.db_path,
                config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
                read_only=self._read_only,
            )
        else:
            conn = self.conn
        
        # Execute with or without timeout
        if self._query_timeout > 0:
            rows, has_more_rows, headers = self._execute_with_timeout(conn, query)
        else:
            rows, has_more_rows, headers = self._execute_direct(conn, query)
        
        # Close connection if it was temporary
        if self.conn is None:
            conn.close()
        
        returned_rows = len(rows)
        
        # Format results as table
        out = tabulate(rows, headers=headers, tablefmt="pretty")
        
        # Apply character limit if output is too long
        char_truncated = len(out) > self._max_chars
        if char_truncated:
            out = out[:self._max_chars]
        
        # Add informative feedback message
        if has_more_rows:
            out += f"\n\n⚠️  Showing first {returned_rows} rows."
        elif char_truncated:
            out += f"\n\n⚠️  Output truncated at {self._max_chars:,} characters."

        return out
    
    def _execute_direct(self, conn, query: str) -> tuple:
        """Execute query without timeout - original code path"""
        q = conn.execute(query)
        rows = q.fetchmany(self._max_rows)
        has_more_rows = q.fetchone() is not None
        headers = [d[0] + "\n" + str(d[1]) for d in q.description]
        return rows, has_more_rows, headers
    
    def _execute_with_timeout(self, conn, query: str) -> tuple:
        """Execute query with timeout using threading.Timer and conn.interrupt()"""
        timer = threading.Timer(self._query_timeout, conn.interrupt)
        timer.start()
        
        try:
            q = conn.execute(query)
            rows = q.fetchmany(self._max_rows)
            has_more_rows = q.fetchone() is not None
            headers = [d[0] + "\n" + str(d[1]) for d in q.description]
            return rows, has_more_rows, headers
        except duckdb.InterruptException:
            raise ValueError(
                f"Query execution timed out after {self._query_timeout} seconds. "
                f"Increase timeout with --query-timeout argument when starting the mcp server."
            )
        finally:
            timer.cancel()

    def query(self, query: str) -> str:
        try:
            return self._execute(query)

        except Exception as e:
            raise ValueError(f"❌ Error executing query: {e}")
