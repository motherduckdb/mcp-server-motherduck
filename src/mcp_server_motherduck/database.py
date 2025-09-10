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
        motherduck_token: str | None = None,
        home_dir: str | None = None,
        saas_mode: bool = False,
        read_only: bool = False,
    ):
        self._read_only = read_only
        self._motherduck_token = motherduck_token
        self._saas_mode = saas_mode
        
        # Set the home directory for DuckDB
        if home_dir:
            os.environ["HOME"] = home_dir

        logger.info("Database client initialized for dynamic connections")

    def _connect_to_database(self, db_path: str) -> duckdb.DuckDBPyConnection:
        """Create a connection to the specified database"""
        db_path, db_type = self._resolve_db_path_type(db_path, self._motherduck_token, self._saas_mode)
        
        logger.info(f"🔌 Connecting to {db_type} database: {db_path}")
        
        conn = duckdb.connect(
            db_path,
            config={"custom_user_agent": f"mcp-server-motherduck/{SERVER_VERSION}"},
            read_only=self._read_only,
        )

        logger.info(f"✅ Successfully connected to {db_type} database")
        
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

    def _execute(self, query: str, db_path: str) -> str:
        """Execute a query on the specified database"""
        conn = None
        try:
            conn = self._connect_to_database(db_path)
            q = conn.execute(query)
            
            out = tabulate(
                q.fetchall(),
                headers=[d[0] + "\n" + d[1] for d in q.description],
                tablefmt="pretty",
            )
            
            return out
            
        finally:
            if conn:
                conn.close()
                logger.info(f"🔌 Closed connection to database")

    def query(self, query: str, db_path: str = ":memory:") -> str:
        """Execute a query on the specified database path"""
        try:
            return self._execute(query, db_path)
        except Exception as e:
            raise ValueError(f"❌ Error executing query: {e}")
    
    def list_available_databases(self) -> str:
        """List available databases including MotherDuck and local files"""
        databases = []
        
        # Check for MotherDuck availability
        if self._motherduck_token or os.getenv("motherduck_token"):
            databases.append("📡 MotherDuck:\n  - md: (default MotherDuck database)\n  - md:database_name (specific MotherDuck database)")
        
        # Check for local DuckDB files
        databases.append("\n💾 Local options:\n  - :memory: (in-memory database)")
        
        # Look for DuckDB files recursively in current directory
        cwd = os.getcwd()
        patterns = ["*.duckdb", "*.db", "*.duck"]
        found_dbs = []
        
        for pattern in patterns:
            # Recursive search using ** glob pattern
            found_dbs.extend(glob.glob(os.path.join(cwd, "**", pattern), recursive=True))
        
        if found_dbs:
            # Sort by path depth (files in current dir first) and then alphabetically
            found_dbs.sort(key=lambda x: (x.count(os.sep), x))
            databases.append("\n📁 Local DuckDB files found:")
            for db_file in found_dbs[:20]:  # Limit to first 20 to avoid overwhelming output
                rel_path = os.path.relpath(db_file, cwd)
                databases.append(f"  - {rel_path}")
            
            if len(found_dbs) > 20:
                databases.append(f"  ... and {len(found_dbs) - 20} more files")
        
        return "\n".join(databases)
    
    def validate_database_path(self, db_path: str) -> bool:
        """Validate that a database path is accessible"""
        # Special paths that are always valid
        if db_path in [":memory:", "*"]:
            return True
        
        # MotherDuck paths
        if db_path.startswith("md:"):
            if not (self._motherduck_token or os.getenv("motherduck_token")):
                raise ValueError("MotherDuck token required for md: paths. Set motherduck_token environment variable or pass --motherduck-token")
            return True
        
        # Local file paths
        if os.path.exists(db_path):
            return True
        
        # Try to create a test connection to validate
        try:
            conn = self._connect_to_database(db_path)
            conn.close()
            return True
        except Exception as e:
            raise ValueError(f"Cannot access database at '{db_path}': {str(e)}")
