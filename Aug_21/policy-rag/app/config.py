"""
config.py - Centralized configuration loaded from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from .env"""

    # OpenAI / LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "75"))

    # Retrieval
    VECTOR_TOP_K: int = int(os.getenv("VECTOR_TOP_K", "10"))
    BM25_TOP_K: int = int(os.getenv("BM25_TOP_K", "10"))
    RERANK_TOP_K: int = int(os.getenv("RERANK_TOP_K", "5"))

    # RRF
    RRF_K: int = int(os.getenv("RRF_K", "60"))

    # Threshold
    RETRIEVAL_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.01"))

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_RAW_DIR: str = os.path.join(BASE_DIR, "data", "raw")
    LLAMA_INDEX_DIR: str = os.path.join(BASE_DIR, "indexes", "llama")

settings = Settings()
