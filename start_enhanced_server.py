#!/usr/bin/env python3
"""
Simple script to start the enhanced MCP server and demonstrate request logging
"""

import subprocess
import sys
import signal
import time
from pathlib import Path

def main():
    print("🚀 Starting Enhanced MCP Tariffs Server with Request Logging")
    print("📝 MCP requests will be logged to: logs/mcp_requests.log")
    print("📝 Database queries will be logged to: logs/queries.log")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Database path
    db_path = Path("data/usitc_data/usitc_trade_data.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("Run the following to build the database:")
        print("  uv run python src/tariffs_mcp/db_build.py --all --years 10")
        return 1
    
    # Start the server
    cmd = [
        "uv", "run", "python", "-m", "tariffs_mcp.tariffs_mcp_server",
        "--db-path", str(db_path),
        "--read-only"
    ]
    
    try:
        # Run the server
        process = subprocess.Popen(
            cmd,
            cwd=Path.cwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("Server started! Logs are being written to logs/mcp_requests.log")
        print("To test the server, connect with an MCP client or use another terminal to run:")
        print("  tail -f logs/mcp_requests.log")
        print("\nServer output:")
        print("-" * 50)
        
        # Stream output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        return process.returncode
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("✅ Server stopped")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
