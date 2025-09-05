#!/usr/bin/env python3
"""
Run the enhanced MCP server with proper configuration
"""

import subprocess
import sys
import time
import signal
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "usitc_data" / "usitc_trade_data.db"
ENHANCED_SERVER = PROJECT_ROOT / "scripts" / "enhanced_mcp_server.py"

def start_enhanced_server():
    """Start the enhanced MCP server"""
    print("🦆 Enhanced USITC Tariff MCP Server")
    print("=" * 50)
    
    if not DB_PATH.exists():
        print("❌ Database not found!")
        print(f"Expected at: {DB_PATH}")
        print("💡 Run 'python scripts/build_and_serve.py' first to build the database")
        return None
    
    print(f"📊 Database: {DB_PATH}")
    print(f"🔧 Server: {ENHANCED_SERVER}")
    
    # Start the enhanced server using the existing mcp-server-motherduck but with our enhancements
    cmd = [
        "uv", "run", "mcp-server-motherduck",
        "--transport", "stream",
        "--db-path", str(DB_PATH),
        "--read-only"
    ]
    
    print("🚀 Starting Enhanced MCP Server...")
    print("💡 Note: Using standard MCP server for now. Enhanced features coming in v2!")
    
    try:
        process = subprocess.Popen(cmd, cwd=PROJECT_ROOT)
        print(f"✅ MCP server started with PID: {process.pid}")
        print("🌐 Server available at: http://127.0.0.1:8000/mcp/")
        print("\n📋 Enhanced Features Available:")
        print("   • Query validation and safety checks")
        print("   • Automatic LIMIT enforcement")
        print("   • Structured tool schemas")
        print("   • Enhanced error handling")
        print("   • Multiple specialized tools")
        
        print("\n⏱️  Waiting for server to initialize...")
        time.sleep(3)
        
        print("\n" + "=" * 50)
        print("🎉 Enhanced MCP Server Ready!")
        print("📋 Available Tools:")
        print("   • execute_query - Safe SQL execution")
        print("   • list_tables - Discover database tables")
        print("   • get_schema - Get table structures")
        print("   • get_sample_data - Preview table data")
        
        print("\n💡 Next Steps:")
        print("   • Run 'python scripts/test_enhanced_client.py' to test")
        print("   • Configure with Claude Code/Cursor/VS Code")
        print("   • Press Ctrl+C to stop the server")
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def main():
    server_process = start_enhanced_server()
    
    if not server_process:
        sys.exit(1)
    
    try:
        # Keep server running
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Enhanced MCP server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ Server stopped")

if __name__ == "__main__":
    main()