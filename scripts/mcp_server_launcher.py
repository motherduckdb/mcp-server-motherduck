#!/usr/bin/env python3
"""
MCP-friendly server launcher for USITC tariff database

This script ensures the database exists and then starts the MCP server
in a way that's compatible with MCP clients using STDIO transport.
No interactive prompts, minimal output to stdout.
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "usitc_data" / "usitc_trade_data.db"
LOGS_DIR = PROJECT_ROOT / "logs"

def setup_duckdb_logging():
    """Set up DuckDB logging configuration"""
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Path to the DuckDB config file
    home_dir = Path.home()
    duckdbrc_path = home_dir / ".duckdbrc"
    
    # Query log path
    query_log_path = LOGS_DIR / "queries.log"
    
    # DuckDB configuration content
    duckdb_config = f"""
PRAGMA enable_logging;
SET log_query_path = '{query_log_path}';
"""
    
    try:
        # Write the configuration to .duckdbrc
        with open(duckdbrc_path, 'w') as f:
            f.write(duckdb_config.strip())
        
        print(f"DuckDB logging enabled. Logs will be written to: {query_log_path}", file=sys.stderr)
        print(f"DuckDB config written to: {duckdbrc_path}", file=sys.stderr)
        
    except Exception as e:
        print(f"Warning: Failed to set up DuckDB logging: {e}", file=sys.stderr)

def ensure_database_exists():
    """Ensure the database exists, build it if necessary"""
    if not DB_PATH.exists():
        # Write to stderr to avoid corrupting STDIO MCP communication
        print("Building USITC tariff database...", file=sys.stderr)
        try:
            subprocess.run([
                "uv", "run", "python", "src/tariffs_mcp/db_build.py", 
                "--all", "--years", "10"
            ], 
            cwd=PROJECT_ROOT, 
            check=True,
            # Redirect stdout to stderr to keep STDIO clean for MCP
            stdout=sys.stderr,
            stderr=sys.stderr
            )
            print("Database build complete", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Failed to build database: {e}", file=sys.stderr)
            sys.exit(1)

def start_mcp_server(db_path: str, read_only: bool = True):
    """Start the MCP server using the script entry point"""
    import subprocess
    
    cmd = ["uv", "run", "mcp-server-motherduck", "--db-path", db_path]
    if read_only:
        cmd.append("--read-only")
    
    try:
        # Run the server directly using the script entry point
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Failed to start MCP server: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Build USITC tariff database and start MCP server (MCP-client friendly)"
    )
    parser.add_argument("--build-only", action="store_true", 
                       help="Only build the database, don't start the server")
    parser.add_argument("--db-path", type=str, default=str(DB_PATH),
                       help="Path to the database file")
    parser.add_argument("--no-read-only", action="store_true",
                       help="Don't start server in read-only mode")
    parser.add_argument("--no-logging", action="store_true",
                       help="Don't set up DuckDB logging")
    
    args = parser.parse_args()
    
    # Set up DuckDB logging unless disabled
    if not args.no_logging:
        setup_duckdb_logging()
    
    # Ensure database exists
    db_path = Path(args.db_path)
    if not db_path.exists():
        if args.build_only:
            ensure_database_exists()
            return
        else:
            ensure_database_exists()
    
    if args.build_only:
        return
    
    # Start MCP server
    start_mcp_server(str(db_path), not args.no_read_only)

if __name__ == "__main__":
    main()
