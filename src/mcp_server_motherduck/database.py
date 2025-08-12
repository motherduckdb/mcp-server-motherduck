import os
import glob
import duckdb
from typing import Literal, Optional
import io
from contextlib import redirect_stdout
from tabulate import tabulate
import logging
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

        self.conn = self._initialize_connection()

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

        logger.info(f"✅ Successfully connected to {self.db_type} database")

        return conn

    def _resolve_db_path_type(
        self, db_path: str, motherduck_token: str | None = None, saas_mode: bool = False
    ) -> tuple[str, Literal["duckdb", "motherduck"]]:
        """Resolve and validate the database path"""
        # Handle wildcard path - find DuckDB database in current directory
        if db_path == "*":
            logger.info("Wildcard '*' specified, searching for DuckDB database in current directory")
            cwd = os.getcwd()
            
            # Common DuckDB file extensions
            patterns = ["*.duckdb", "*.db", "*.duck"]
            found_dbs = []
            
            for pattern in patterns:
                found_dbs.extend(glob.glob(os.path.join(cwd, pattern)))
            
            if not found_dbs:
                raise ValueError(
                    f"No DuckDB database files found in current directory: {cwd}\n"
                    f"Searched for files with extensions: {', '.join(patterns)}"
                )
            
            if len(found_dbs) > 1:
                logger.warning(f"Multiple database files found: {found_dbs}")
                logger.info(f"Using the first database: {found_dbs[0]}")
            
            db_path = found_dbs[0]
            logger.info(f"Auto-detected DuckDB database: {db_path}")
        
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
