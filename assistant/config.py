"""
All assistant settings in one place. Each can be changed with an environment
variable, so nobody has to edit code to try a different model.

    CAMPUSBUDDY_EMBED   "auto" (default), "tfidf", or a sentence-transformers model name
    CAMPUSBUDDY_LLM     "auto" (default), "none" (no LLM, extractive answers), or a
                        Hugging Face chat model name
    CAMPUSBUDDY_TOP_K   how many chunks to retrieve (default 3)
    CAMPUSBUDDY_CHUNK_WORDS / CAMPUSBUDDY_CHUNK_OVERLAP   chunk size in words (default 120 / 30)
    CAMPUSBUDDY_THRESHOLD   override the "I don't know" threshold
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "data" / "docs"
INDEX_DIR = Path(__file__).resolve().parent / "index"     # built files, not committed

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # small, fast, 384-dim
DEFAULT_LLM = "Qwen/Qwen2.5-1.5B-Instruct"                      # free, runs on a laptop GPU

EMBED = os.getenv("CAMPUSBUDDY_EMBED", "auto")
LLM = os.getenv("CAMPUSBUDDY_LLM", "auto")
TOP_K = int(os.getenv("CAMPUSBUDDY_TOP_K", "3"))
CHUNK_WORDS = int(os.getenv("CAMPUSBUDDY_CHUNK_WORDS", "120"))
CHUNK_OVERLAP = int(os.getenv("CAMPUSBUDDY_CHUNK_OVERLAP", "30"))

# Below this similarity the assistant says "I don't know" instead of guessing.
# The two embedders give scores on different scales, so each has its own default.
# eval/assistant/evaluate_assistant.py --tune finds the best value and saves it.
DEFAULT_THRESHOLDS = {"tfidf": 0.16, "sentence-transformers": 0.2324}
THRESHOLD_OVERRIDE = os.getenv("CAMPUSBUDDY_THRESHOLD")

IDK = "I don't know. I couldn't find this in the college documents."
