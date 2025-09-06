#!/usr/bin/env python3
"""
Test script to verify MCP request logging is working
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server.server import MCPUnifiedServer
from mcp_server.core.database_client import UniversalDatabaseClient

async def test_mcp_logging():
    """Test MCP request logging"""
    print("Testing MCP request logging...")
    
    # Database path
    db_path = "data/usitc_data/usitc_trade_data.db"
    
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}. Please build the database first.")
        return
    
    # Initialize unified server
    server = MCPUnifiedServer()
    await server.initialize()
    
    # Get the database client
    db_client = server.db_client
    
    try:
        # Import the MCP types for testing
        import mcp.types as types
        
        # Test by calling the enhanced database client directly to trigger logging
        print("\n1. Testing execute_query logging...")
        result = await db_client.execute_query("SELECT COUNT(*) as table_count FROM information_schema.tables")
        print(f"   Query result: {result}")
        
        print("\n2. Testing list_tables logging...")
        tables = await db_client.list_tables()
        print(f"   Found {len(tables)} tables")
        
        print("\n3. Testing get_sample_data logging...")
        # Get first table name
        if tables:
            first_table = tables[0]
            sample_result = await db_client.get_sample_data(first_table, 3)
            print(f"   Sample data result for {first_table}")
            print(f"   Sample data: {sample_result[:200]}..." if len(sample_result) > 200 else f"   Sample data: {sample_result}")
        
        print("\nTest completed! Check logs/mcp_requests.log for the logged requests.")
        print("Note: The above tests log database operations. To test full MCP request logging,")
        print("you need to run the server with an actual MCP client.")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_client.close()

if __name__ == "__main__":
    asyncio.run(test_mcp_logging())
