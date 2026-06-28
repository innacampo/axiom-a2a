import os
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
if not GCP_PROJECT:
    raise ValueError("GCP_PROJECT or GOOGLE_CLOUD_PROJECT must be set")

# Write it back so the Vertex AI SDK finds it under either name
os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT

GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
AXIOM_MODEL: str = os.getenv("AXIOM_MODEL", "gemini-2.5-flash")
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
PUBMED_MCP_URL: str = os.getenv("PUBMED_MCP_URL", "http://localhost:8001")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

PUBMED_API_KEY: str = os.getenv("PUBMED_API_KEY", "")
PUBMED_MCP_PATH: str = os.getenv("PUBMED_MCP_PATH", "")
