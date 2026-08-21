"""
llm.py - Interface to the LLM (OpenAI SDK).
"""
import logging
from typing import List, Dict, Any, Tuple
from openai import OpenAI

from app.config import settings
from app.generation.prompt import SYSTEM_PROMPT, build_context_string

logger = logging.getLogger(__name__)


class LLMService:
    """Service to interact with the LLM for RAG generation."""
    
    def __init__(self):
        # Configure client with custom base URL for the proxy
        client_kwargs = {}
        if settings.OPENAI_API_KEY:
            client_kwargs["api_key"] = settings.OPENAI_API_KEY
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL
            
        self.client = OpenAI(**client_kwargs)
        self.model = settings.OPENAI_CHAT_MODEL
        logger.info(f"Initialized LLM service with model {self.model}")

    def generate_answer(
        self, 
        query: str, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate an answer grounded in the retrieved chunks.
        
        Returns:
            Tuple of (answer string, list of unique sources used)
        """
        if not retrieved_chunks:
            return (
                "I couldn't find sufficient information in the available company "
                "policies to answer this question.",
                []
            )
            
        context_str = build_context_string(retrieved_chunks)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context information is below.\n\n{context_str}\n\nGiven the context information and no prior knowledge, answer the query.\nQuery: {query}"}
        ]
        
        try:
            logger.info(f"Calling LLM {self.model} to generate answer...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0, # Zero temperature for factual RAG
            )
            answer = response.choices[0].message.content
            
            # Extract unique sources for the response schema
            unique_sources = {}
            for chunk in retrieved_chunks:
                source_key = f"{chunk['document']}_{chunk['section']}_{chunk['page']}"
                if source_key not in unique_sources:
                    unique_sources[source_key] = {
                        "document": chunk["document"],
                        "section": chunk["section"],
                        "page": chunk["page"]
                    }
                    
            return answer, list(unique_sources.values())
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            fallback_answer = (
                "Sorry, the LLM proxy is currently unreachable. "
                "However, I retrieved the following relevant policy text:\n\n" +
                "\n".join([chunk["text"] for chunk in retrieved_chunks])
            )
            # Extract unique sources for the response schema
            unique_sources = {}
            for chunk in retrieved_chunks:
                source_key = f"{chunk['document']}_{chunk['section']}_{chunk['page']}"
                if source_key not in unique_sources:
                    unique_sources[source_key] = {
                        "document": chunk["document"],
                        "section": chunk["section"],
                        "page": chunk["page"]
                    }
            return fallback_answer, list(unique_sources.values())
