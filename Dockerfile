FROM python:3.11-slim
WORKDIR /app

# curl needed for the MCP health check in start.sh
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install MCP server dependencies (copy requirements first for layer caching)
COPY app/pubmed-mcp-server/requirements.txt /tmp/mcp-requirements.txt
RUN pip install -r /tmp/mcp-requirements.txt --no-cache-dir

# Install AXIOM backend dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Pre-download sentence-transformers model at build time.
# server.py sets HF_HUB_OFFLINE=1 at runtime so the model MUST be cached.
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy MCP server source (includes server.py, scoring.py, requirements.txt)
COPY app/pubmed-mcp-server/ /app/pubmed-mcp-server/

# ChromaDB writes relative to server.py's cwd (/app/pubmed-mcp-server)
# Create the directory so it doesn't fail on first write
RUN mkdir -p /app/pubmed-mcp-server/chroma_data

# Copy AXIOM backend and frontend
COPY backend/ ./backend/
COPY index.html style.css script.js ./

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV PUBMED_MCP_PATH=/app/pubmed-mcp-server
ENV PUBMED_MCP_URL=http://localhost:8001
ENV MCP_TRANSPORT=streamable-http
ENV MCP_PORT=8001
ENV PORT=8080

EXPOSE 8080

CMD ["/app/start.sh"]
