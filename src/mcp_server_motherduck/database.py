import os
import duckdb
from typing import Literal, Optional
import io
from contextlib import redirect_stdout
from tabulate import tabulate
import logging
from pathlib import Path
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
    ):
        self._read_only = read_only
        self.db_path, self.db_type = self._resolve_db_path_type(
            db_path, motherduck_token, saas_mode
        )
        logger.info(f"Database client initialized in `{self.db_type}` mode")

        # Set the home directory for DuckDB
        if home_dir:
            os.environ["HOME"] = home_dir
            
        # Determine logging configuration
        self.logs_dir = self._get_logs_dir()
        self.query_log_path = self.logs_dir / "queries.log" if self.logs_dir else None

        self.conn = self._initialize_connection()
        
    def _get_logs_dir(self) -> Optional[Path]:
        """Get the logs directory path if it exists"""
        # Try to find the project root by looking for common project files
        current_path = Path.cwd()
        for parent in [current_path] + list(current_path.parents):
            if (parent / "pyproject.toml").exists() or (parent / "README.md").exists():
                logs_dir = parent / "logs"
                if logs_dir.exists():
                    return logs_dir
                break
        return None
        
    def _setup_logging_for_connection(self, conn: duckdb.DuckDBPyConnection):
        """Set up logging for a DuckDB connection"""
        if self.query_log_path:
            try:
                conn.execute("PRAGMA enable_logging")
                conn.execute(f"SET log_query_path = '{self.query_log_path}'")
                logger.debug(f"DuckDB logging enabled for connection, logs to: {self.query_log_path}")
            except Exception as e:
                logger.warning(f"Failed to enable DuckDB logging: {e}")

    def _initialize_connection(self) -> Optional[duckdb.DuckDBPyConnection]:
        """Initialize connection to the MotherDuck or DuckDB database"""

        logger.info(f"🔌 Connecting to {self.db_type} database")

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
                self._setup_logging_for_connection(conn)
                conn.execute("SELECT 1")
                conn.close()
                return None
            except Exception as e:
                logger.error(f"❌ Read-only check failed: {e}")
                raise

        conn = duckdb.connect(
            self.db_path,
            config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
            read_only=self._read_only,
        )
        
        # Set up logging for persistent connections
        self._setup_logging_for_connection(conn)

        logger.info(f"✅ Successfully connected to {self.db_type} database")

        return conn

    def _resolve_db_path_type(
        self, db_path: str, motherduck_token: str | None = None, saas_mode: bool = False
    ) -> tuple[str, Literal["duckdb", "motherduck"]]:
        """Resolve and validate the database path"""
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
        if self.conn is None:
            # open short lived readonly connection, run query, close connection, return result
            conn = duckdb.connect(
                self.db_path,
                config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
                read_only=self._read_only,
            )
            # Set up logging for short-lived connections too
            self._setup_logging_for_connection(conn)
            q = conn.execute(query)
        else:
            q = self.conn.execute(query)

        out = tabulate(
            q.fetchall(),
            headers=[d[0] + "\n" + d[1] for d in q.description],
            tablefmt="pretty",
        )

        if self.conn is None:
            conn.close()

        return out

    def query(self, query: str) -> str:
        try:
            return self._execute(query)

        except Exception as e:
            raise ValueError(f"❌ Error executing query: {e}")
