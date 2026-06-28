#!/bin/bash
set -e

echo "[AXIOM] Starting MCP server (port 8001)..."
cd /app/pubmed-mcp-server
python server.py &
MCP_PID=$!

echo "[AXIOM] Waiting for MCP server to be ready..."
for i in $(seq 1 30); do
    if curl -sf -o /dev/null http://localhost:8001/mcp 2>/dev/null; then
        echo "[AXIOM] MCP server ready after ${i}s"
        break
    fi
    if ! kill -0 $MCP_PID 2>/dev/null; then
        echo "[AXIOM] MCP server process died — check logs"
        exit 1
    fi
    sleep 1
done

echo "[AXIOM] Starting FastAPI server (port ${PORT:-8080})..."
cd /app
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8080}"
