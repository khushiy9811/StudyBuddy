"""Central configuration for StudyBuddy. All values are overridable via env vars
so chunking/top-k/model experiments (see Section 5 of the project plan) don't
require touching code.
"""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
NOTES_DIR = DATA_DIR / "notes"
CHROMA_DIR = DATA_DIR / "chroma"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3:mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "study_notes")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

TOP_K = {
    "explain": int(os.getenv("TOP_K_EXPLAIN", "4")),
    "quiz": int(os.getenv("TOP_K_QUIZ", "6")),
    "summarize": int(os.getenv("TOP_K_SUMMARIZE", "8")),
}

TEMPERATURE = {
    "answer": float(os.getenv("TEMP_ANSWER", "0.1")),
    "quiz": float(os.getenv("TEMP_QUIZ", "0.5")),
}

NOTES_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
