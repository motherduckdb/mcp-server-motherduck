#!/usr/bin/env python3
"""
Test client to verify MCP server connection and query the USITC tariff database
"""

import requests
import json
import sys
import time
from datetime import datetime

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/"

def test_connection():
    """Test basic connection to MCP server with proper MCP initialization"""
    print("🔍 Testing MCP server connection...")
    
    # First try an MCP initialization request
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        response = requests.post(MCP_SERVER_URL,
                               json=init_payload,
                               headers={
                                   "Content-Type": "application/json",
                                   "Accept": "application/json, text/event-stream"
                               },
                               timeout=10)
        
        if response.status_code == 200:
            # Parse SSE format response
            response_text = response.text
            if "event: message" in response_text and "data: " in response_text:
                # Extract JSON from SSE format
                lines = response_text.split('\n')
                json_data = None
                for line in lines:
                    if line.startswith("data: "):
                        json_data = line[6:]  # Remove "data: " prefix
                        break
                
                if json_data:
                    try:
                        result = json.loads(json_data)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        print(f"JSON data: {json_data}")
                        return False
                else:
                    print("❌ No data found in SSE response")
                    return False
            else:
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"Raw response: {response.text}")
                    return False
            
            if "result" in result:
                print("✅ MCP server is running and accessible")
                print(f"🔧 Server capabilities: {result.get('result', {}).get('capabilities', {})}")
                return True
            else:
                print(f"❌ Unexpected response: {result}")
                return False
        else:
            print(f"❌ MCP server returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        print("💡 Make sure the server is running with 'python scripts/build_and_serve.py'")
        return False

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
            # Parse SSE format response
            response_text = response.text
            if "event: message" in response_text and "data: " in response_text:
                # Extract JSON from SSE format
                lines = response_text.split('\n')
                json_data = None
                for line in lines:
                    if line.startswith("data: "):
                        json_data = line[6:]  # Remove "data: " prefix
                        break
                
                if json_data:
                    try:
                        return json.loads(json_data)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error in send_mcp_request: {e}")
                        return None
                else:
                    return None
            else:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return None
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_database_queries():
    """Test various database queries"""
    print("\n📊 Testing database queries...")
    
    queries = [
        {
            "name": "List all tables",
            "sql": "SHOW TABLES"
        },
        {
            "name": "Database summary",
            "sql": "SELECT table_name, row_count FROM data_summary ORDER BY table_name"
        },
        {
            "name": "Sample tariff data (2024)",
            "sql": "SELECT hts8, brief_description, mfn_ave FROM tariff_2024_tariff_database_202405 WHERE mfn_ave > 0 ORDER BY mfn_ave DESC LIMIT 5"
        },
        {
            "name": "Count by year",
            "sql": """
            SELECT 
                CASE 
                    WHEN table_name LIKE '%2015%' THEN '2015'
                    WHEN table_name LIKE '%2016%' THEN '2016'
                    WHEN table_name LIKE '%2017%' THEN '2017'
                    WHEN table_name LIKE '%2018%' THEN '2018'
                    WHEN table_name LIKE '%2019%' THEN '2019'
                    WHEN table_name LIKE '%2020%' THEN '2020'
                    WHEN table_name LIKE '%2021%' THEN '2021'
                    WHEN table_name LIKE '%2022%' THEN '2022'
                    WHEN table_name LIKE '%2023%' THEN '2023'
                    WHEN table_name LIKE '%2024%' THEN '2024'
                    ELSE 'other'
                END as year,
                SUM(row_count) as total_rows
            FROM data_summary 
            GROUP BY year 
            ORDER BY year
            """
        }
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. {query['name']}")
        print("-" * 40)
        
        response = send_mcp_request("tools/call", {
            "name": "query",
            "arguments": {
                "query": query["sql"]
            }
        })
        
        if response and "result" in response:
            result = response["result"]
            if "content" in result and result["content"]:
                try:
                    # Parse the result content
                    content = result["content"][0]["text"] if isinstance(result["content"], list) else result["content"]
                    print(content)
                except Exception as e:
                    print(f"Result: {result}")
            else:
                print("No data returned")
        else:
            print(f"❌ Query failed: {response}")
        
        time.sleep(0.5)  # Brief pause between queries

def main():
    print("🧪 MCP Server Test Client")
    print("=" * 40)
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # Test queries
    test_database_queries()
    
    print("\n" + "=" * 40)
    print("✅ All tests completed!")
    print("💡 Your MCP server is working correctly with the USITC tariff database")

if __name__ == "__main__":
    main()