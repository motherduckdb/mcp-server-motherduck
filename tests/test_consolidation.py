#!/usr/bin/env python3
"""
Simple test script for the consolidated MCP server
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server.server import MCPUnifiedServer
from mcp_server.core.database_client import UniversalDatabaseClient

async def test_server_initialization():
    """Test server initialization"""
    print("Testing MCP Unified Server initialization...")
    
    try:
        server = MCPUnifiedServer()
        await server.initialize()
        print("✅ Server initialization successful")
        
        # Test plugin loading
        plugins = server.plugins
        print(f"✅ Loaded {len(plugins)} plugins: {list(plugins.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        return False

async def test_database_connection():
    """Test database connectivity"""
    print("\nTesting database connectivity...")
    
    try:
        db_client = UniversalDatabaseClient()
        await db_client.connect()
        
        # Try to list tables
        tables = await db_client.list_tables()
        print(f"✅ Database connection successful, found {len(tables)} tables")
        
        if tables:
            print("📋 Available tables:")
            for table in tables[:5]:  # Show first 5
                print(f"  • {table}")
            if len(tables) > 5:
                print(f"  ... and {len(tables) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   (This is expected if no DuckDB files exist yet)")
        return False

async def main():
    """Main test function"""
    print("🔧 MCP Unified Server - Consolidation Test")
    print("=" * 50)
    
    # Test server initialization
    server_ok = await test_server_initialization()
    
    # Test database connection 
    db_ok = await test_database_connection()
    
    print("\n" + "=" * 50)
    if server_ok:
        print("✅ Consolidation successful! Server is ready to use.")
        print("\nNext steps:")
        print("1. Run with: python -m mcp_server")
        print("2. Or test CLI: python -m mcp_server info")
        print("3. Check plugins: python -m mcp_server plugins")
    else:
        print("❌ Consolidation issues found. Check error messages above.")
    
    return server_ok

if __name__ == "__main__":
    asyncio.run(main())
