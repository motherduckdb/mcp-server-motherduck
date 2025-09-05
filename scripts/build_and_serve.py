#!/usr/bin/env python3
"""
End-to-end script that builds the USITC tariff database and starts the MCP server
"""

import subprocess
import sys
import time
import socket
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "usitc_data" / "usitc_trade_data.db"

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=PROJECT_ROOT)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        sys.exit(1)

def check_port_available(port=8000):
    """Check if the specified port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except socket.error:
        return False

def kill_existing_servers():
    """Kill any existing MCP servers running on port 8000"""
    try:
        # Find processes using port 8000
        result = subprocess.run(['lsof', '-i', ':8000'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            pids = []
            for line in lines:
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    pids.append(pid)
            
            if pids:
                print(f"🔍 Found existing processes on port 8000: {', '.join(pids)}")
                for pid in pids:
                    try:
                        subprocess.run(['kill', pid], check=True)
                        print(f"🛑 Killed process {pid}")
                    except subprocess.CalledProcessError:
                        print(f"⚠️  Could not kill process {pid} (may already be dead)")
                time.sleep(2)  # Give processes time to die
    except Exception as e:
        print(f"⚠️  Error checking for existing servers: {e}")

def start_mcp_server():
    """Start the MCP server in the background"""
    # Check if port is available
    if not check_port_available():
        print("🔍 Port 8000 is already in use. Attempting to clean up...")
        kill_existing_servers()
        
        # Check again after cleanup
        if not check_port_available():
            print("❌ Port 8000 is still in use. Please manually stop the conflicting process:")
            subprocess.run(['lsof', '-i', ':8000'])
            sys.exit(1)
    
    print(f"\n🚀 Starting MCP server with database: {DB_PATH}")
    
    cmd = [
        "uv", "run", "mcp-server-motherduck",
        "--transport", "stream",
        "--db-path", str(DB_PATH),
        "--read-only"
    ]
    
    try:
        # Start the server process
        process = subprocess.Popen(cmd, cwd=PROJECT_ROOT)
        print(f"✅ MCP server started with PID: {process.pid}")
        print("🌐 Server should be available at: http://127.0.0.1:8000/mcp")
        print("📊 Database contains 10 years of USITC tariff data (2015-2024)")
        print("\n⏱️  Waiting a few seconds for server to initialize...")
        time.sleep(5)  # Give it a bit more time
        
        # Check if the process is still running
        if process.poll() is not None:
            print("❌ Server process exited unexpectedly")
            sys.exit(1)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        sys.exit(1)

def main():
    print("🦆 USITC Tariff Database Builder & MCP Server")
    print("=" * 50)
    
    # Step 1: Build the database
    if not DB_PATH.exists():
        print("📦 Database not found. Building from scratch...")
        run_command("uv run python src/tariffs_mcp/db_build.py --all --years 10", 
                   "Building USITC tariff database (10 years)")
    else:
        print(f"✅ Database already exists at: {DB_PATH}")
        print("💡 To rebuild, delete the database file and run again")
    
    # Step 2: Start MCP server
    server_process = start_mcp_server()
    
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("📋 Summary:")
    print(f"   • Database: {DB_PATH}")
    print("   • MCP Server: http://127.0.0.1:8000/mcp")
    print("   • Contains: 10 tables with 142K+ rows of tariff data")
    print("\n💡 Next steps:")
    print("   • Run 'python scripts/test_enhanced_client.py' to test the connection")
    print("   • Use the server with Claude Code, Cursor, or other MCP clients")
    print("   • Press Ctrl+C to stop the server")
    
    try:
        # Keep the server running
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down MCP server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    main()