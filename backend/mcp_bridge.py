# Connects to AXIOM MCP server running on PUBMED_MCP_URL.
# Start the MCP server first: python server.py (from the pubmed-mcp-server directory)
# MCP_TRANSPORT=streamable-http (default) — server runs on port 8001

import logging
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from backend.config import PUBMED_MCP_URL

logger = logging.getLogger(__name__)

MCP_ENDPOINT = PUBMED_MCP_URL.rstrip("/") + "/mcp"


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """
    Open a Streamable HTTP session to the AXIOM MCP server, initialize it,
    call a tool, and return the text content of the first result.
    
    Opens and closes a session per call — fine for MVP.
    TODO v0.2: persistent session pool to avoid per-call handshake overhead.
    """
    try:
        async with streamablehttp_client(MCP_ENDPOINT) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return ""
    except Exception as e:
        logger.error(f"MCP tool call failed [{tool_name}]: {e}", exc_info=True)
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
        print(f"Testing MCP connection to {MCP_ENDPOINT}...")
        result = await query_local_evidence("vasomotor symptoms menopause hormone therapy")
        if result:
            print("Success! Result preview:")
            print(result[:500])
        else:
            print("No result. Is the MCP server running? → python server.py")

    asyncio.run(test())