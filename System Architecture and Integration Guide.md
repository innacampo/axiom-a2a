# System Architecture and Integration Guide

## 1. System Architecture Diagram

*   **Visual layout of agent roles:** 
    *   **Frontend:** Vanilla HTML/CSS/JS served as static files by FastAPI. Real-time updates rendered via a custom SSE stream reader using the Fetch API.
    *   **API Gateway:** FastAPI serving as the backend and routing requests via SSE (Server-Sent Events).
    *   **ADK Orchestrator:** A custom Python agent (`backend/agent.py`) utilizing Google Vertex AI (`gemini-2.0-flash`).
    *   **Data Layer:** ChromaDB (via the MCP Server) for semantic search over PubMed abstracts.
*   **Orchestration flow between agents:** AXIOM operates on a strictly guarded `Perceive → Plan → Act → Observe → Iterate` loop:
    1. Agent receives query and user-defined confidence threshold.
    2. Agent queries local ChromaDB for evidence (`query_evidence`).
    3. If evidence is missing or confidence scores are below threshold, it reaches out to the live PubMed API (`ingest_to_chroma` / `search_pubmed`).
    4. If confidence still falls short, the agent iteratively reformulates the query (e.g., prepending "systematic review meta-analysis") up to `MAX_RETRIES`.
    5. Agent synthesizes the answer grounded strictly in retrieved abstracts, exiting the loop via defined stopping conditions (Threshold Met, Budget Exhausted, or Token Ceiling).
*   **Identification of host vs. client agents:** 
    *   **Host:** The Python ADK Orchestrator (powered by Vertex AI).
    *   **Client/Tool:** The external AXIOM PubMed MCP Server (FastMCP).

## 2. MCP Server Configuration & Registry

*   **List of all active MCP servers:** AXIOM-MCP (PubMed MCP Server running locally or via HTTP).
*   **Exposed tools, resources, and prompts:** 
    *   `query_evidence`: Queries the local ChromaDB for vectorized PubMed evidence based on the user's clinical question.
    *   `search_pubmed`: Directly searches live PubMed data as a raw fallback mechanism.
    *   `check_retractions`: Verifies cited evidence against known retracted literature. Runs as a safety gate before evidence is passed to synthesis.
    *   `ingest_to_chroma`: Fetches data from the live PubMed API and embeds it into the ChromaDB vector store for semantic querying.
*   **Connection strings and environment variables:** 
    *   `PUBMED_MCP_URL`: HTTP streamable endpoint (defaults to `http://localhost:8001`).
    *   `PUBMED_MCP_PATH`: Path to the MCP server.
    *   *(Note: Kept out of version control via `.env`)*

## 3. State Management & Context Hand-offs

*   **Methods for maintaining session context:** Sessions are inherently stateless per request on the backend. Real-time state updates (active step, confidence scores) are streamed asynchronously to the frontend using Server-Sent Events (`EventSourceResponse` in `main.py`).
*   **Protocol for passing data between agents:** Structured JSON Payloads sent via HTTP POST to the MCP server. Yields strictly formatted JSON over SSE: `{"type": "step_update", "data": {"step": 2, "status": "active"}}`.
*   **Token optimization and context-window strategy:** 
    *   **Context Truncation:** To prevent token limit exhaustion, evidence passed to the Generative Model synthesis prompt is strictly capped (`evidence_text[:4000]`).
    *   **Progressive Disclosure:** Uses a local vector database (ChromaDB) to retrieve only the top relevant chunks rather than injecting full articles.

## 4. Security & Authentication Model

*   **API key and credential management:** Managed locally via a `.env` file (based on `.env.example`). Requires `PUBMED_API_KEY` for NCBI API access and Google Cloud credentials (`GCP_PROJECT`, `GCP_LOCATION`) for Vertex AI.
*   **Transport layer security definitions:** Cross-Origin Resource Sharing (CORS) is currently set to `allow_origins=["*"]` for demo purposes. Communication with the Vertex AI endpoint uses encrypted Google Cloud APIs. 
*   **Agent access control levels (Guardrails):** 
    *   **Strict Grounding:** The system prompt forcefully restricts the agent: *"You answer based only on retrieved PubMed evidence — never from internal memory."*
    *   **Deterministic Limits:** Hard caps on processing via `MAX_RETRIES` (default: 3) to prevent infinite loops.
    *   *(Note: Currently configured without strict PHI scrubbing for demo purposes).*

## 5. Local Development & Testing Workflow

*   **Instructions for mock server setups:**
    1. Copy `.env.example` to `.env` and supply keys.
    2. Start the PubMed MCP server first (runs on port `8001`).
    3. Install requirements (`pip install -r requirements.txt`).
    4. Start the FastAPI backend: `uvicorn backend.main:app --reload`.
*   **Steps to trace agent protocol logs:** Tracing is automatically captured in a list during the agent loop (e.g., `[attempt 1] ChromaDB sparse...`). This entire audit trace is emitted to the frontend on completion via the `{"type": "audit", "data": {"trace": "..."}}` event block and displayed in the UI.
*   **Validation checks for new tools:** Any new tools must integrate with the retry-loop stopping conditions (EXIT_A, EXIT_B, EXIT_C) and ensure returned confidence scores map successfully to `confidence.py` evaluating functions.
