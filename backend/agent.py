import vertexai
from vertexai.generative_models import GenerativeModel
from backend.config import GCP_PROJECT, GCP_LOCATION, AXIOM_MODEL, MAX_RETRIES
from backend.mcp_bridge import query_local_evidence, search_pubmed_live, ingest_to_chroma
from backend.confidence import evidence_is_sufficient, result_count
import logging
import asyncio
from typing import AsyncGenerator

vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
import logging
logger = logging.getLogger(__name__)
logger.info(f"Vertex AI initialized: project={GCP_PROJECT} location={GCP_LOCATION} model={AXIOM_MODEL}")

SYSTEM_INSTRUCTION = """
You are AXIOM, an evidence-grounded clinical AI for menopause care.
You answer based only on retrieved PubMed evidence — never from internal memory.
For every clinical claim, cite the PMID and year.
If retrieved evidence is sparse, explicitly say evidence is limited rather than
extrapolating. Menopause-specific hormonal staging context (STRAW+10) is relevant
when interpreting results.
"""

def parse_evidence_cards(evidence_text: str) -> list[dict]:
    """Parse query_evidence formatted output into frontend card dicts.
    
    Expected block format from server.py:
      ### Result N
      **PMID**: 12345678 | **Journal**: Journal Name | **Year**: 2023
      **Study Type**: meta-analysis | **Composite Score**: 0.743 (...)
      
      Article title here
      
      Abstract text...
    """
    import re
    # Strip the query_evidence header line before parsing
    evidence_text = re.sub(
        r"Found \d+ results, ranked by evidence quality \(from \d+ stored articles\):\n*",
        "",
        evidence_text
    )
    cards = []
    blocks = re.split(r"---+", evidence_text)
    
    for block in blocks[:5]:
        pmid_match   = re.search(r"\*\*PMID\*\*:\s*(\d+)", block)
        year_match   = re.search(r"\*\*Year\*\*:\s*(\d{4})", block)
        score_match  = re.search(r"\*\*Composite Score\*\*:\s*([\d.]+)", block)
        journal_match = re.search(r"\*\*Journal\*\*:\s*([^|]+)", block)
        
        if not pmid_match:
            continue
        
        # Title is the first non-empty line after the Composite Score line
        title = "Untitled"
        lines = block.split("\n")
        past_score_line = False
        for line in lines:
            if "Composite Score" in line:
                past_score_line = True
                continue
            if past_score_line and line.strip():
                # Strip any remaining markdown bold markers
                title = re.sub(r"\*\*|<[^>]+>", "", line.strip())
                break
        
        # Excerpt: text after the title line, cleaned of markdown
        excerpt_raw = re.sub(
            r"#{1,3} Result \d+|"
            r"\*\*PMID\*\*:.*|"
            r"\*\*Study Type\*\*:.*|"
            r"\*\*Composite Score\*\*:.*|"
            r"<[^>]+>",
            "", block
        ).strip()
        
        cards.append({
            "pmid":    pmid_match.group(1),
            "title":   title,
            "year":    year_match.group(1) if year_match else "Unknown",
            "score":   float(score_match.group(1)) if score_match else 0.0,
            "journal": journal_match.group(1).strip() if journal_match else "",
            "excerpt": excerpt_raw[:300]
        })
    
    return cards


async def run_axiom_agent(query: str, threshold: float) -> AsyncGenerator[dict, None]:
    """
    Perceive → Plan → Act → Observe → Iterate loop.
    
    Stopping conditions (name these in comments as security guardrails too):
      EXIT_A: confidence threshold met
      EXIT_B: retry budget exhausted (MAX_RETRIES attempts)
      EXIT_C: token ceiling / unexpected exception
    """
    trace = []
    attempt = 0
    evidence_text = ""
    confidence = 0.0
    threshold_met = False

    # --- STEP 1: Parse query ---
    yield {"type": "step_update", "data": {"step": 1, "status": "active"}}
    # sanitize: strip leading/trailing whitespace, no PHI check needed for demo
    query = query.strip()
    trace.append(f"[AXIOM] query received ({len(query)} chars)")
    yield {"type": "step_update", "data": {"step": 1, "status": "complete"}}

    # --- STEPS 2–3: Retrieve + Evaluate (with retry) ---
    current_query = query
    
    while attempt < MAX_RETRIES and not threshold_met:
        attempt += 1
        trace.append(f"[attempt {attempt}/{MAX_RETRIES}]")
        
        yield {"type": "step_update", "data": {"step": 2, "status": "active"}}
        
        # Strategy: try local ChromaDB first, fall back to live PubMed
        local_result = await query_local_evidence(current_query)
        
        if result_count(local_result) < 3:
            # ChromaDB sparse or empty — fetch live and re-query
            trace.append(f"[attempt {attempt}] ChromaDB sparse ({result_count(local_result)} results) → fetching from PubMed")
            await ingest_to_chroma(current_query)
            local_result = await query_local_evidence(current_query)
            
            # If still empty after ingest, fall back to raw PubMed text
            if result_count(local_result) == 0:
                trace.append(f"[attempt {attempt}] Falling back to raw PubMed search")
                evidence_text = await search_pubmed_live(current_query)
                confidence = 0.45  # PubMed raw text has no composite score — set conservative floor
                threshold_met = False
            else:
                evidence_text = local_result
                threshold_met, confidence = evidence_is_sufficient(local_result, threshold)
        else:
            evidence_text = local_result
            threshold_met, confidence = evidence_is_sufficient(local_result, threshold)
        
        yield {"type": "step_update", "data": {"step": 2, "status": "complete"}}
        
        yield {"type": "step_update", "data": {"step": 3, "status": "active"}}
        trace.append(f"[attempt {attempt}] confidence={confidence:.3f} threshold={threshold:.3f} met={threshold_met}")
        
        yield {
            "type": "confidence",
            "data": {"value": confidence, "threshold": threshold, "met": threshold_met}
        }
        
        if threshold_met:
            yield {"type": "step_update", "data": {"step": 3, "status": "complete"}}
            trace.append(f"[EXIT_A] threshold met on attempt {attempt}")
            break
        else:
            yield {"type": "step_update", "data": {"step": 3, "status": "retry"}}
            # Reformulate for next attempt
            if attempt == 1:
                current_query = f"systematic review meta-analysis {query}"
            elif attempt == 2:
                current_query = f"randomized controlled trial clinical evidence {query}"
            # attempt == MAX_RETRIES → loop exits next iteration (EXIT_B)
    
    if not threshold_met:
        trace.append(f"[EXIT_B] retry budget exhausted after {attempt} attempts, proceeding with best available evidence")

    # --- STEP 4: Synthesize answer ---
    yield {"type": "step_update", "data": {"step": 4, "status": "active"}}
    
    model = GenerativeModel(AXIOM_MODEL, system_instruction=[SYSTEM_INSTRUCTION])
    prompt = f"""Clinical question: {query}

Retrieved evidence:
{evidence_text[:4000]}

Synthesize a clinical answer grounded only in the evidence above.
Cite PMIDs. Note if evidence is limited or if confidence was below threshold ({threshold})."""
    
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        answer_text = response.text
    except Exception as e:
        trace.append(f"[EXIT_C] synthesis failed: {e}")
        answer_text = "Synthesis failed. Please retry or consult primary literature directly."

    yield {"type": "step_update", "data": {"step": 4, "status": "complete"}}
    yield {"type": "answer", "data": {"text": answer_text}}
    
    # Parse evidence into structured cards for the frontend
    evidence_items = parse_evidence_cards(evidence_text)
    yield {"type": "evidence", "data": {"items": evidence_items}}
    yield {"type": "audit", "data": {"trace": "\n".join(trace)}}