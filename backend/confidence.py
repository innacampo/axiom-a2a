import re
import logging

logger = logging.getLogger(__name__)

def extract_confidence(query_evidence_output: str) -> float:
    """Parse the maximum composite score from query_evidence text output.
    
    The output contains lines like:
      **Composite Score**: 0.743 (relevance: 0.71 × study: 1.25 × recency: 0.83)
    
    Extract all composite score values, return the max.
    If none found (empty knowledge base, parse failure), return 0.0.
    """
    pattern = r"\*\*Composite Score\*\*:\s*([\d.]+)"
    matches = re.findall(pattern, query_evidence_output)
    if not matches:
        return 0.0
    scores = [float(m) for m in matches]
    # We use the maximum composite score, not the mean.
    # Rationale: one high-quality RCT or systematic review should satisfy the
    # evidence threshold even if other retrieved results are weaker or off-topic.
    # This mirrors how a clinician evaluates evidence — the best study dominates. 
    return round(max(scores), 3)   # max, not mean

def evidence_is_sufficient(output: str, threshold: float) -> tuple[bool, float]:
    """Return (threshold_met, confidence_value) for a query_evidence result."""
    conf = extract_confidence(output)
    return (conf >= threshold, conf)

def result_count(output: str) -> int:
    """Count evidence results returned (for determining if ChromaDB is populated)."""
    # query_evidence returns "Knowledge base is empty." if collection.count() == 0
    if "Knowledge base is empty" in output:
        return 0
    # Count "### Result N" headers
    return len(re.findall(r"### Result \d+", output))

# No scoring math here — that lives in scoring.py on the MCP server side.
# This module only parses the MCP server's text output.