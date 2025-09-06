import duckdb
import logging
import time
import re
import os
from typing import Dict, List, Optional, Any, Literal, Tuple
from pathlib import Path
from tabulate import tabulate
from .configs import SERVER_VERSION, DEFAULT_DB_CONFIG

logger = logging.getLogger("mcp_server")

class QueryValidator:
    """Validates SQL queries for safety and performance"""
    
    BANNED_KEYWORDS = [
        "DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER", 
        "TRUNCATE", "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    ]
    
    def __init__(self, max_rows: int = 1000):
        self.max_rows = max_rows
    
    def validate_query(self, sql: str) -> 'ValidationResult':
        """Validate a SQL query for safety"""
        sql_upper = sql.upper().strip()
        
        # Check for banned keywords
        for keyword in self.BANNED_KEYWORDS:
            if keyword in sql_upper:
                return ValidationResult(False, f"Forbidden keyword: {keyword}")
        
        # Must be a SELECT or similar read-only statement
        if not sql_upper.startswith(('SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
            return ValidationResult(False, "Only SELECT, WITH, SHOW, DESCRIBE, and EXPLAIN statements are allowed")
        
        return ValidationResult(True, "Query is valid")
    
    def apply_limit(self, sql: str, limit: int = None) -> str:
        """Apply LIMIT clause if not present"""
        if limit is None:
            limit = self.max_rows
            
        sql_upper = sql.upper()
        if "LIMIT" not in sql_upper:
            return f"{sql.rstrip(';')} LIMIT {limit}"
        return sql

class ValidationResult:
    """Result of query validation"""
    def __init__(self, is_valid: bool, error_message: str = ""):
        self.is_valid = is_valid
        self.error_message = error_message

class UniversalDatabaseClient:
    """Universal database client supporting local DuckDB and MotherDuck"""
    
    def __init__(
        self,
        db_path: str | None = None,
        motherduck_token: str | None = None,
        home_dir: str | None = None, 
        saas_mode: bool = False,
        read_only: bool = True,
        max_rows: int = 1000
    ):
        self._read_only = read_only
        self.max_rows = max_rows
        self.validator = QueryValidator(max_rows)
        
        # Set default database path if not provided
        if db_path is None:
            db_path = "data/usitc_data/usitc_trade_data.db"
        
        self.db_path = db_path
        self.motherduck_token = motherduck_token or os.getenv("MOTHERDUCK_TOKEN")
        self.home_dir = Path(home_dir) if home_dir else Path.home()
        self.saas_mode = saas_mode
        self._connection = None
        
        logger.info(f"Database client initialized: {self.db_path}")
    
    def _init_motherduck(self) -> Optional[duckdb.DuckDBPyConnection]:
        """Initialize MotherDuck connection"""
        if not self.motherduck_token:
            logger.warning("MotherDuck token not found, using local DuckDB only")
            return None
        
        try:
            config = {"motherduck_token": self.motherduck_token}
            if self.saas_mode:
                config["custom_user_agent"] = f"mcp-server/{SERVER_VERSION}"
            
            conn = duckdb.connect(f"md:?motherduck_token={self.motherduck_token}")
            logger.info("Successfully connected to MotherDuck")
            return conn
            
        except Exception as e:
            logger.error(f"Failed to connect to MotherDuck: {e}")
            return None
    
    def _get_logs_dir(self) -> Optional[Path]:
        """Get logs directory path"""
        try:
            if self.saas_mode:
                return Path("/tmp/logs")
            else:
                return self.home_dir / ".local" / "state" / "mcp-server"
        except Exception:
            return None
    
    def _get_db_info(
        self, duck_db_path: str | None = None
    ) -> tuple[str, Literal["duckdb", "motherduck"]]:
        """Determine database type and connection string"""
        if self.motherduck_token and not duck_db_path:
            return f"md:?motherduck_token={self.motherduck_token}", "motherduck"
        
        # Use provided path or default local path
        db_path = duck_db_path or self.db_path
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        return db_path, "duckdb"
    
    async def connect(self) -> None:
        """Connect to database"""
        try:
            # Try MotherDuck first if token available
            if self.motherduck_token:
                self._connection = self._init_motherduck()
            
            # Fall back to local DuckDB
            if not self._connection:
                self._connection = self._initialize_connection()
            
            if not self._connection:
                raise Exception("Failed to establish any database connection")
                
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def _initialize_connection(self) -> Optional[duckdb.DuckDBPyConnection]:
        """Initialize local DuckDB connection"""
        try:
            db_path, db_type = self._get_db_info()
            
            if db_type == "duckdb":
                # Check if file exists
                if not os.path.exists(db_path):
                    logger.warning(f"Database file not found: {db_path}")
                    # Create an in-memory database for testing
                    conn = duckdb.connect(":memory:")
                    logger.info("Created in-memory database for testing")
                    return conn
                
                conn = duckdb.connect(db_path, read_only=self._read_only)
                logger.info(f"Connected to local DuckDB: {db_path}")
                return conn
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to initialize connection: {e}")
            return None
    
    async def execute_query(self, query: str, include_metadata: bool = False) -> str:
        """Execute SQL query and return formatted results with optional metadata"""
        if not self._connection:
            await self.connect()
        
        try:
            start_time = time.time()
            result = self._connection.execute(query).fetchall()
            execution_time = time.time() - start_time
            
            if not result:
                base_result = "Query executed successfully - no results returned"
                if include_metadata:
                    base_result += f"\n\n📊 Execution Info:\n• Execution time: {execution_time:.3f}s\n• Rows returned: 0"
                return base_result
            
            # Get column names
            columns = [desc[0] for desc in self._connection.description]
            
            # Format as table
            table = tabulate(result, headers=columns, tablefmt="grid")
            
            base_result = table
            
            # Add metadata if requested
            if include_metadata:
                base_result += f"\n\n📊 Execution Info:\n• Execution time: {execution_time:.3f}s\n• Rows returned: {len(result)}\n• Columns: {len(columns)}"
                
                # Add column info
                base_result += "\n• Column details:"
                for i, col in enumerate(columns):
                    # Get sample values to understand data types
                    sample_values = [str(row[i]) if row[i] is not None else 'NULL' for row in result[:3]]
                    base_result += f"\n  - {col}: {', '.join(sample_values)[:50]}{'...' if len(', '.join(sample_values)) > 50 else ''}"
            else:
                base_result += f"\n\n⏱️ Execution time: {execution_time:.3f}s | Rows: {len(result)}"
            
            return base_result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise Exception(f"Query failed: {str(e)}")
    
    async def list_tables(self) -> List[str]:
        """List all tables in the database"""
        if not self._connection:
            await self.connect()
        
        try:
            result = self._connection.execute("SHOW TABLES").fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []
    
    async def get_schema(self, table_name: str) -> str:
        """Get schema information for a table"""
        if not self._connection:
            await self.connect()
        
        try:
            result = self._connection.execute(f"DESCRIBE {table_name}").fetchall()
            columns = [desc[0] for desc in self._connection.description]
            table = tabulate(result, headers=columns, tablefmt="grid")
            return table
        except Exception as e:
            raise Exception(f"Failed to get schema for {table_name}: {str(e)}")
    
    async def get_sample_data(self, table_name: str, limit: int = 5, random_sample: bool = False) -> str:
        """Get sample data from a table"""
        if random_sample:
            query = f"SELECT * FROM {table_name} USING SAMPLE {min(limit, 100)}"
        else:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return await self.execute_query(query)
    
    def close(self):
        """Close database connection and cleanup resources"""
        if self._connection:
            try:
                self._connection.close()
                logger.info("Database connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._connection = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup"""
        self.close()
