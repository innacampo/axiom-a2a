# AXIOM — Evidence-Grounded Clinical AI for Menopause Care

AXIOM addresses the problem of fragmented menopause care and the challenge of accessing relevant, up-to-date evidence buried within PubMed. Traditional clinical AIs often hallucinate confidence or provide answers not directly backed by primary literature. AXIOM ensures that clinical responses are grounded strictly in retrieved scientific evidence, providing transparent confidence scoring rather than unwarranted certainty.

## How it works

AXIOM operates on a perceive→plan→act→observe→iterate loop. The agent receives a clinical query and a user-defined confidence threshold. It then acts by retrieving relevant evidence via a PubMed MCP server. It observes the retrieved data by scoring its confidence based on relevance, study type, and recency. If the confidence falls below the threshold, it iterates by reformulating the query and retrying the search. Once the threshold is met (or the retry budget is exhausted), it synthesizes an answer grounded only in the retrieved abstracts, citing the specific PMIDs used.

## Architecture

```
User → FastAPI → ADK Orchestrator → AXIOM-MCP (PubMed) → PubMed API
```

## Agent concepts demonstrated

- ADK orchestrator
- MCP server integration
- Retry loop with stopping condition
- Evidence-grounded synthesis (no hallucinated confidence)

## Run locally

```bash
git clone <repository_url>
cd <repository_directory>
cp .env.example .env
# Fill in your API keys in the .env file
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

## Deploy to Cloud Run

```bash
gcloud run deploy axiom --source . --set-env-vars GCP_PROJECT=axiom-agent-500220,GCP_LOCATION=us-central1
```