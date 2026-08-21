"""
ingest.py - Main ingestion orchestrator using LlamaIndex.
"""
from typing import List, Dict, Any
import logging
import os

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.file import PyMuPDFReader

from app.config import settings

logger = logging.getLogger(__name__)


def run_ingestion_pipeline() -> Dict[str, Any]:
    """
    Run the full end-to-end ingestion pipeline using LlamaIndex:
    1. Setup Environment Settings
    2. Load PDFs from data/raw
    3. Chunk & Embed documents to build VectorStoreIndex
    4. Persist to disk
    
    Returns:
        Dict containing ingestion report statistics.
    """
    logger.info("Starting LlamaIndex ingestion pipeline...")
    
    # 1. Setup Environment
    if settings.OPENAI_API_KEY:
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    if settings.OPENAI_BASE_URL:
        os.environ["OPENAI_BASE_URL"] = settings.OPENAI_BASE_URL

    Settings.llm = OpenAI(model=settings.OPENAI_CHAT_MODEL, temperature=0.0)
    Settings.embed_model = OpenAIEmbedding(model=settings.OPENAI_EMBEDDING_MODEL)
    Settings.node_parser = SentenceSplitter(
        chunk_size=settings.CHUNK_SIZE, 
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    
    # 2. Load Documents
    logger.info(f"Loading documents from {settings.DATA_RAW_DIR}...")
    documents = SimpleDirectoryReader(
        input_dir=settings.DATA_RAW_DIR,
        required_exts=[".pdf"],
        file_extractor={".pdf": PyMuPDFReader()}
    ).load_data()
    
    if not documents:
        logger.error("No documents loaded. Ensure PDFs are in data/raw/")
        return {"status": "FAILED", "reason": "No PDFs found"}
        
    logger.info(f"Loaded {len(documents)} documents/pages.")
    
    # 3. Create Index
    logger.info("Building VectorStoreIndex (chunking and embedding)...")
    index = VectorStoreIndex.from_documents(documents)
    
    # 4. Persist to Disk
    os.makedirs(settings.LLAMA_INDEX_DIR, exist_ok=True)
    index.storage_context.persist(persist_dir=settings.LLAMA_INDEX_DIR)
    
    # Build report
    report = {
        "status": "SUCCESS",
        "documents_loaded": len(documents),
        "index_type": "VectorStoreIndex (LlamaIndex)",
        "persist_dir": settings.LLAMA_INDEX_DIR,
    }
    
    logger.info(f"Ingestion complete: {report}")
    return report
