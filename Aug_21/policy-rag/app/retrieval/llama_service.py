"""
llama_service.py - Service to handle querying and chatting using LlamaIndex.
"""
import os
import logging
from typing import Dict, Any, List

from llama_index.core import (
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.memory import ChatMemoryBuffer

from app.config import settings

logger = logging.getLogger(__name__)


class LlamaService:
    """Service to interact with the LlamaIndex for RAG retrieval and generation."""
    
    def __init__(self):
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
        
        self.index = self._load_index()
        
    def _load_index(self):
        """Load the persisted index from disk."""
        if not os.path.exists(settings.LLAMA_INDEX_DIR):
            logger.warning(f"Index directory {settings.LLAMA_INDEX_DIR} does not exist. Run ingestion first.")
            return None
            
        try:
            logger.info(f"Loading index from {settings.LLAMA_INDEX_DIR}...")
            storage_context = StorageContext.from_defaults(persist_dir=settings.LLAMA_INDEX_DIR)
            index = load_index_from_storage(storage_context)
            logger.info("Index loaded successfully.")
            return index
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return None

    def query(self, query_str: str) -> Dict[str, Any]:
        """
        Execute a single stateless query using the query engine.
        Includes a SimilarityPostprocessor.
        """
        if not self.index:
            return {"answer": "Index not found. Please run ingestion.", "sources": []}
            
        query_engine = self.index.as_query_engine(
            similarity_top_k=settings.VECTOR_TOP_K
        )
        
        logger.info(f"Querying index for: {query_str}")
        response = query_engine.query(query_str)
        
        # Extract sources from the response nodes
        sources = []
        for node in response.source_nodes:
            metadata = node.node.metadata
            sources.append({
                "document": metadata.get("file_name", "Unknown"),
                "section": metadata.get("section", "N/A"),
                "page": metadata.get("page_label", "N/A"),
                "score": node.score
            })
            
        return {
            "answer": str(response),
            "sources": sources
        }

    def get_chat_engine(self):
        """
        Returns a stateful ChatEngine with ChatMemoryBuffer.
        """
        if not self.index:
            return None
            
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        chat_engine = self.index.as_chat_engine(
            chat_mode="condense_plus_context",
            memory=memory,
            verbose=False
        )
        return chat_engine
