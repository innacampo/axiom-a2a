# Connects to AXIOM MCP server running on PUBMED_MCP_URL.
# Start the MCP server first: python server.py (from the pubmed-mcp-server directory)
# MCP_TRANSPORT=streamable-http (default)

import httpx
import json
import os
import logging
from backend.config import PUBMED_MCP_URL

logger = logging.getLogger(__name__)

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Send a tool call to the AXIOM MCP server via HTTP and return the text result."""
    url = f"{PUBMED_MCP_URL}/mcp/v1/tools/call"
    payload = {
        "name": tool_name,
        "arguments": arguments
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            # FastMCP typical response format for tools/call
            if isinstance(data, dict):
                # Handle varying response structures from different MCP server implementations
                if "content" in data and isinstance(data["content"], list) and len(data["content"]) > 0:
                    return data["content"][0].get("text", "")
                elif "result" in data:
                    return str(data["result"])
                
            return json.dumps(data)
            
    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name}: {e}")
        return ""

async def query_local_evidence(question: str, top_k: int = 5) -> str:
    return await call_mcp_tool("query_evidence", {"question": question, "top_k": top_k})

async def search_pubmed_live(query: str, max_results: int = 5) -> str:
    return await call_mcp_tool("search_pubmed", {"query": query, "max_results": max_results})

async def ingest_to_chroma(query: str, max_results: int = 10) -> str:
    return await call_mcp_tool("ingest_to_chroma", {"query": query, "max_results": max_results})


if __name__ == "__main__":
    import asyncio
    
    async def test():
        print(f"Testing MCP connection to {PUBMED_MCP_URL}...")
        result = await query_local_evidence("vasomotor symptoms menopause hormone therapy")
        if result:
            print("Success! Result preview:")
            print(result[:500])
        else:
            print("Failed to get a result. Make sure the MCP server is running.")
            
    asyncio.run(test())