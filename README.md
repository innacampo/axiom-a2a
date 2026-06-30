# AXIOM — Evidence-Grounded Clinical AI for Menopause Care

Menopause symptoms get split across specialists. A cardiologist sees the cholesterol, an orthopedist sees the frozen shoulder, a GP sees the anxiety, a gynecologist calls the cycle changes normal — and the estrogen decline connecting all four rarely gets named out loud, because no one in the room is looking at the whole picture. The evidence to connect them exists; it's just scattered across tens of thousands of PubMed papers and inaccessible at the point of care.

AXIOM is a clinical AI agent built to close that gap. It retrieves PubMed evidence, scores it against a confidence threshold, and synthesizes an answer grounded strictly in what it actually found — never from the model's internal memory, and never with confidence it hasn't earned.

## How it works

AXIOM runs a perceive → plan → act → observe → iterate loop. The agent takes a clinical query and a user-defined confidence threshold, queries a local ChromaDB index of PubMed evidence, and scores what comes back. If confidence falls short, it reformulates the query (prepending terms like "systematic review meta-analysis" or "randomized controlled trial") and retries — up to three attempts — before falling back to a live PubMed search. Once the threshold is met, or the retry budget runs out, it synthesizes an answer and cites the specific PMIDs it used.

## Architecture

```
User → FastAPI → ADK Orchestrator → AXIOM-MCP
                                         ├── ChromaDB (primary, local)
                                         └── PubMed API (fallback, live)
```

## Composite evidence scoring

Raw cosine similarity isn't enough on its own — a heavily-cited 2012 case report can outscore a 2025 RCT on semantic distance alone. AXIOM corrects for this with a composite score per retrieved paper:

```
composite_score = similarity × study_type_boost × recency_boost
```

- **study_type_boost** — ranges from 0.90x (editorial/comment) to 1.30x (meta-analysis), graded by evidence hierarchy: meta-analysis (1.30) → systematic review (1.25) → RCT (1.20) → clinical trial (1.15) → cohort study (1.10) → case-control (1.05) → case reports (1.00) → review (0.95) → editorial/comment (0.90)
- **recency_boost** — exponential decay, `e^(-0.03 × age_in_years)`, so older evidence is discounted but never zeroed out

Confidence reported to the user is the **max** composite score across retrieved papers, not the mean — one strong piece of evidence shouldn't get diluted by several weak ones.

Retraction checking runs as a separate hard gate, not a score term: the `check_retractions` tool cross-references retrieved evidence against known retracted literature before anything reaches synthesis. Most demo-stage clinical AI systems skip this step entirely.

## Agent concepts demonstrated

- ADK orchestrator with explicit stopping conditions (threshold met, retry budget exhausted, exception)
- MCP server integration (FastMCP, Streamable HTTP)
- Retry loop with query reformulation
- Evidence-grounded synthesis — no hallucinated confidence

## What makes this different

Most clinical AI systems either hallucinate confidence or outsource the uncertainty to the user. AXIOM does neither: it surfaces the confidence score directly, shows the retry trace, and will tell you "evidence is limited" rather than synthesize an answer from a thin evidence base.

## Run locally

```bash
git clone <repository_url>
cd <repository_directory>
cp .env.example .env
# Fill in your API keys in the .env file
pip install -r requirements.txt

# Terminal 1 — start MCP server first
cd app/medical-evidence-mcp && python server.py

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