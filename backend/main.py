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

app = FastAPI(title="AXIOM API")

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
            yield {"data": json.dumps({"type": "step_update", "data": {"step": 1, "status": "active"}})}
            yield {"data": json.dumps({"type": "step_update", "data": {"step": 1, "status": "complete"}})}
            
            yield {"data": json.dumps({"type": "step_update", "data": {"step": 2, "status": "active"}})}
            yield {"data": json.dumps({"type": "step_update", "data": {"step": 2, "status": "complete"}})}
            
            yield {"data": json.dumps({"type": "step_update", "data": {"step": 3, "status": "active"}})}
            
            # call agent
            async for event in run_axiom_agent(request.query, request.confidence_threshold):
                yield {"data": json.dumps(event)}
                
            yield {"data": json.dumps({"type": "step_update", "data": {"step": 4, "status": "active"}})}
            yield {"data": json.dumps({"type": "step_update", "data": {"step": 4, "status": "complete"}})}
            
            yield {"data": json.dumps({"type": "answer", "data": {"text": "This is a placeholder answer."}})}
            yield {"data": json.dumps({"type": "evidence", "data": {"items": []}})}
            yield {"data": json.dumps({"type": "audit", "data": {"trace": "Placeholder audit trace"}})}
            
        except Exception as e:
            logger.error(f"Error in query stream: {e}")
            yield {"data": json.dumps({"type": "error", "data": {"message": str(e)}})}

    return EventSourceResponse(event_generator())

app.mount("/", StaticFiles(directory=".", html=True), name="static")