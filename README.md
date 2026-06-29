# AXIOM — Evidence-Grounded Clinical AI for Menopause Care

AXIOM addresses the problem of fragmented menopause care and the challenge of accessing relevant, up-to-date evidence buried within PubMed. Traditional clinical AIs often hallucinate confidence or provide answers not directly backed by primary literature. AXIOM ensures that clinical responses are grounded strictly in retrieved scientific evidence, providing transparent confidence scoring rather than unwarranted certainty.

## How it works

AXIOM operates on a perceive→plan→act→observe→iterate loop. The agent receives a clinical query and a user-defined confidence threshold. It then acts by retrieving relevant evidence via a PubMed MCP server. It observes the retrieved data by scoring its confidence based on relevance, study type, and recency. If the confidence falls below the threshold, it iterates by reformulating the query and retrying the search. Once the threshold is met (or the retry budget is exhausted), it synthesizes an answer grounded only in the retrieved abstracts, citing the specific PMIDs used.

## Architecture

```
User → FastAPI → ADK Orchestrator → AXIOM-MCP
                                         ├── ChromaDB (primary, local)
                                         └── PubMed API (fallback, live)
```

## Agent concepts demonstrated

- ADK orchestrator
- MCP server integration
- Retry loop with stopping condition
- Evidence-grounded synthesis (no hallucinated confidence)

## What makes this different

Most clinical AI systems either hallucinate confidence or outsource uncertainty to the user.
AXIOM does neither: it surfaces the confidence score directly, shows the retry trace, and
will tell you "evidence is limited" rather than synthesize an answer from insufficient data.

The `check_retractions` tool is baked into the MCP server — any evidence retrieved can be
cross-checked against known retracted literature before synthesis. Most demo systems skip
this step entirely.

## Run locally

```bash
git clone <repository_url>
cd <repository_directory>
cp .env.example .env
# Fill in your API keys in the .env file
pip install -r requirements.txt

# Terminal 1 — start MCP server first
cd app/pubmed-mcp-server && python server.py

# Terminal 2 — start FastAPI backend
uvicorn backend.main:app --reload
```

## Deploy to Cloud Run

```bash
gcloud run deploy axiom --source . \
  --region us-central1 \
  --set-env-vars GCP_PROJECT=your-project-id,\
GCP_LOCATION=us-central1,\
AXIOM_MODEL=gemini-2.5-flash,\
MCP_TRANSPORT=streamable-http,\
MCP_PORT=8001 \
  --set-secrets ENTREZ_EMAIL=ENTREZ_EMAIL:latest,\
ENTREZ_API_KEY=ENTREZ_API_KEY:latest
```