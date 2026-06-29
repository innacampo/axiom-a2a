FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Clone MCP server from GitHub at build time
RUN git clone https://github.com/innacampo/medical-evidence-mcp.git \
    /app/medical-evidence-mcp

# Install MCP server dependencies
RUN pip install -r /app/medical-evidence-mcp/requirements.txt --no-cache-dir

# Install AXIOM backend dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Pre-download sentence-transformers model
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# ChromaDB directory
RUN mkdir -p /app/medical-evidence-mcp/chroma_data

# Copy AXIOM backend and frontend
COPY backend/ ./backend/
COPY index.html style.css script.js ./
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV PUBMED_MCP_PATH=/app/medical-evidence-mcp
ENV PUBMED_MCP_URL=http://localhost:8001
ENV MCP_TRANSPORT=streamable-http
ENV MCP_PORT=8001
ENV PORT=8080

EXPOSE 8080
CMD ["/app/start.sh"]