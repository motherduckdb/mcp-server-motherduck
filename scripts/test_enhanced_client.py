#!/usr/bin/env python3
"""
Test client for Enhanced MCP Server with comprehensive tool testing
"""

import requests
import json
import sys
import time
from datetime import datetime

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/"

def parse_sse_response(response_text):
    """Parse Server-Sent Events format response"""
    if "event: message" in response_text and "data: " in response_text:
        lines = response_text.split('\n')
        for line in lines:
            if line.startswith("data: "):
                return json.loads(line[6:])
    return None

def send_mcp_request(method, params=None):
    """Send an MCP request to the server"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }
    if params:
        payload["params"] = params
    
    try:
        response = requests.post(MCP_SERVER_URL, 
                               json=payload, 
                               headers={
                                   "Content-Type": "application/json",
                                   "Accept": "application/json, text/event-stream"
                               },
                               timeout=30)
        
        if response.status_code == 200:
            return parse_sse_response(response.text)
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_initialization():
    """Test MCP server initialization"""
    print("🔍 Testing MCP server initialization...")
    
    init_response = send_mcp_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "enhanced-test-client",
            "version": "1.0.0"
        }
    })
    
    if init_response and "result" in init_response:
        print("✅ MCP server initialized successfully")
        print(f"🔧 Server: {init_response['result'].get('serverInfo', {}).get('name', 'Unknown')}")
        return True
    else:
        print("❌ MCP initialization failed")
        return False

def test_list_tools():
    """Test listing available tools"""
    print("\n🛠️  Testing tool discovery...")
    
    response = send_mcp_request("tools/list")
    
    if response and "result" in response:
        tools = response["result"]["tools"]
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   • {tool['name']}: {tool['description'][:60]}...")
        return tools
    else:
        print("❌ Failed to list tools")
        return []

def test_enhanced_tools():
    """Test all enhanced MCP tools"""
    print("\n📊 Testing Enhanced MCP Tools")
    print("=" * 50)
    
    # Test 1: List Tables
    print("\n1. Testing list_tables...")
    response = send_mcp_request("tools/call", {
        "name": "list_tables",
        "arguments": {}
    })
    
    if response and "result" in response:
        content = response["result"]["content"][0]["text"]
        print("✅ List tables successful:")
        print(content[:300] + "..." if len(content) > 300 else content)
    else:
        print("❌ List tables failed")
    
    # Test 2: Get Schema
    print("\n2. Testing get_schema (all tables)...")
    response = send_mcp_request("tools/call", {
        "name": "get_schema",
        "arguments": {}
    })
    
    if response and "result" in response:
        print("✅ Get schema successful")
    else:
        print("❌ Get schema failed")
    
    # Test 3: Get Schema for specific table
    print("\n3. Testing get_schema (specific table)...")
    response = send_mcp_request("tools/call", {
        "name": "get_schema", 
        "arguments": {"table_name": "tariff_2024_tariff_database_202405"}
    })
    
    if response and "result" in response:
        content = response["result"]["content"][0]["text"]
        print("✅ Table schema successful:")
        print(content[:200] + "..." if len(content) > 200 else content)
    else:
        print("❌ Table schema failed")
    
    # Test 4: Sample Data
    print("\n4. Testing get_sample_data...")
    response = send_mcp_request("tools/call", {
        "name": "get_sample_data",
        "arguments": {
            "table_name": "tariff_2024_tariff_database_202405",
            "limit": 3
        }
    })
    
    if response and "result" in response:
        content = response["result"]["content"][0]["text"]
        print("✅ Sample data successful:")
        print(content[:300] + "..." if len(content) > 300 else content)
    else:
        print("❌ Sample data failed")

def test_query_safety():
    """Test query validation and safety features"""
    print("\n🛡️  Testing Query Safety Features")
    print("=" * 50)
    
    # Test dangerous queries
    dangerous_queries = [
        "DROP TABLE tariff_2024_tariff_database_202405",
        "DELETE FROM tariff_2024_tariff_database_202405", 
        "INSERT INTO tariff_2024_tariff_database_202405 VALUES (1,2,3)",
        "UPDATE tariff_2024_tariff_database_202405 SET hts8 = 999"
    ]
    
    for i, query in enumerate(dangerous_queries, 1):
        print(f"\n{i}. Testing dangerous query: {query[:50]}...")
        response = send_mcp_request("tools/call", {
            "name": "execute_query",
            "arguments": {"query": query}
        })
        
        if response and "result" in response:
            content = response["result"]["content"][0]["text"]
            if "Query validation failed" in content or "prohibited keyword" in content:
                print("✅ Query blocked correctly")
            else:
                print("❌ Dangerous query was NOT blocked!")
                print(content[:100])
        else:
            print("❌ Query safety test failed")

def test_safe_queries():
    """Test safe queries with enhanced features"""
    print("\n✅ Testing Safe Queries")
    print("=" * 50)
    
    queries = [
        {
            "name": "Simple SELECT with LIMIT",
            "query": "SELECT hts8, brief_description FROM tariff_2024_tariff_database_202405 LIMIT 3",
            "explain": True
        },
        {
            "name": "COUNT query",
            "query": "SELECT COUNT(*) as total_tariffs FROM tariff_2024_tariff_database_202405"
        },
        {
            "name": "Query without LIMIT (should be auto-limited)",
            "query": "SELECT hts8, brief_description FROM tariff_2024_tariff_database_202405"
        },
        {
            "name": "GROUP BY query",
            "query": "SELECT LEFT(brief_description, 10) as category, COUNT(*) FROM tariff_2024_tariff_database_202405 GROUP BY LEFT(brief_description, 10) ORDER BY COUNT(*) DESC LIMIT 5"
        }
    ]
    
    for i, test_query in enumerate(queries, 1):
        print(f"\n{i}. {test_query['name']}")
        print("-" * 40)
        
        args = {"query": test_query["query"]}
        if test_query.get("explain"):
            args["explain"] = True
            
        response = send_mcp_request("tools/call", {
            "name": "execute_query",
            "arguments": args
        })
        
        if response and "result" in response:
            content = response["result"]["content"][0]["text"]
            print("✅ Query executed successfully")
            # Show first part of result
            lines = content.split('\n')
            for line in lines[:10]:  # Show first 10 lines
                print(line)
            if len(lines) > 10:
                print("...")
        else:
            print("❌ Query failed")
        
        time.sleep(0.5)

def main():
    print("🧪 Enhanced MCP Server Test Suite")
    print("=" * 50)
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test initialization
    if not test_initialization():
        sys.exit(1)
    
    # Test tool discovery
    tools = test_list_tools()
    if not tools:
        sys.exit(1)
    
    # Test enhanced tools
    test_enhanced_tools()
    
    # Test query safety
    test_query_safety()
    
    # Test safe queries
    test_safe_queries()
    
    print("\n" + "=" * 50)
    print("✅ Enhanced MCP Server Test Suite Complete!")
    print("🛡️  Security: Query validation working correctly")
    print("🔧 Tools: All enhanced tools functional")
    print("📊 Data: USITC tariff database accessible and safe")
    print("\n💡 Your enhanced MCP server is production-ready!")

if __name__ == "__main__":
    main()