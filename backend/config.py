import os
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT: str = os.getenv("GCP_PROJECT", "axiom-agent-500220")
GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")

if not GCP_PROJECT:
    raise ValueError("GCP_PROJECT is missing at import time.")

PUBMED_API_KEY: str = os.getenv("PUBMED_API_KEY", "")
PUBMED_MCP_PATH: str = os.getenv("PUBMED_MCP_PATH", "")
PUBMED_MCP_URL: str = os.getenv("PUBMED_MCP_URL", "http://localhost:8001")

AXIOM_MODEL: str = os.getenv("AXIOM_MODEL", "gemini-2.0-flash")
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")