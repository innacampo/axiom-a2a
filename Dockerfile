FROM python:3.11-slim
WORKDIR /app

# Install pubmed-mcp-server dependencies
RUN pip install -r /app/pubmed-mcp-server/requirements.txt --no-cache-dir

# Install AXIOM dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Copy app
COPY backend/ ./backend/
COPY index.html style.css script.js ./

ENV PUBMED_MCP_PATH=/app/pubmed-mcp-server
ENV PORT=8080

EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]