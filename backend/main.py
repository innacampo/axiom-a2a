import json
import logging
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.config import LOG_LEVEL
from backend.agent import run_axiom_agent

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from backend.mcp_bridge import ingest_to_chroma

WARMUP_TOPICS = [
    "hormone therapy vasomotor symptoms menopause randomized controlled trial",
    "estrogen hot flashes clinical evidence systematic review",
    "menopause hormone replacement therapy cardiovascular risk meta-analysis",
    "HRT cognitive function menopause clinical trial",
    "menopausal transition brain health estrogen neuroprotection",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm ChromaDB on startup
    from backend.mcp_bridge import call_mcp_tool
    try:
        count_result = await call_mcp_tool("query_evidence", 
                                           {"question": "menopause", "top_k": 1})
        # Parse article count from header line "from N stored articles"
        import re
        match = re.search(r"from (\d+) stored articles", count_result)
        count = int(match.group(1)) if match else 0
        
        if count < 100:
            logger.info(f"ChromaDB has {count} articles — running warmup ingestion")
            for topic in WARMUP_TOPICS:
                await ingest_to_chroma(topic, max_results=10)
                logger.info(f"Ingested: {topic[:50]}")
        else:
            logger.info(f"ChromaDB ready: {count} articles")
    except Exception as e:
        logger.warning(f"Warmup failed (non-fatal): {e}")
    yield

app = FastAPI(title="AXIOM API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=500)
    confidence_threshold: float = Field(..., ge=0.50, le=1.00)

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            async for event in run_axiom_agent(request.query, request.confidence_threshold):
                yield {"data": json.dumps(event)}
        except Exception as e:
            logger.error(f"Error in query stream: {e}")
            yield {"data": json.dumps({"type": "error", "data": {"message": str(e)}})}

    return EventSourceResponse(event_generator())

app.mount("/", StaticFiles(directory=".", html=True), name="static")