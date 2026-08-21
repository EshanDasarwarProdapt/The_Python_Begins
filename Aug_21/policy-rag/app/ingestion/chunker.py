"""
chunker.py - Section-aware recursive text chunking.

Preserves policy section boundaries. If a section exceeds CHUNK_SIZE,
it is split using sentence-aware recursive chunking with overlap.
"""
import re
import hashlib
from typing import List, Dict, Any
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def _sentence_split(text: str) -> List[str]:
    """Split text into sentences using regex."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _create_chunk_id(document: str, section: str, index: int) -> str:
    """Create a deterministic chunk ID."""
    base = f"{document}_{section}_{index}"
    short_hash = hashlib.md5(base.encode()).hexdigest()[:8]
    # Sanitize for use as an ID
    safe_section = re.sub(r'[^a-z0-9_]', '_', section.lower())[:30]
    safe_doc = re.sub(r'[^a-z0-9_]', '_', document.lower().replace('.pdf', ''))
    return f"{safe_doc}_{safe_section}_{index:03d}_{short_hash}"


def chunk_section(
    section_doc: Dict[str, Any],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Chunk a single section-level document.

    If the section text fits within chunk_size, it is returned as a single chunk.
    Otherwise, it is split into overlapping chunks at sentence boundaries.

    Args:
        section_doc: A section-level dict with 'text' and metadata.
        chunk_size: Maximum characters per chunk (default from config).
        chunk_overlap: Overlap characters between chunks (default from config).

    Returns:
        List of chunk dicts with chunk_id and all metadata preserved.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    text = section_doc["text"]

    chunks = []

    if len(text) <= chunk_size:
        # Section fits in one chunk
        chunks.append({
            "chunk_id": _create_chunk_id(section_doc["document"], section_doc["section"], 0),
            "text": text,
            "document": section_doc["document"],
            "department": section_doc["department"],
            "policy_type": section_doc["policy_type"],
            "section": section_doc["section"],
            "page": section_doc["page"],
        })
    else:
        # Split into sentences, then reassemble into chunks
        sentences = _sentence_split(text)
        current_chunk_sentences = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_length + sentence_len > chunk_size and current_chunk_sentences:
                # Emit current chunk
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append({
                    "chunk_id": _create_chunk_id(
                        section_doc["document"], section_doc["section"], chunk_index
                    ),
                    "text": chunk_text,
                    "document": section_doc["document"],
                    "department": section_doc["department"],
                    "policy_type": section_doc["policy_type"],
                    "section": section_doc["section"],
                    "page": section_doc["page"],
                })
                chunk_index += 1

                # Overlap: keep last N characters worth of sentences
                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current_chunk_sentences):
                    if overlap_len + len(s) <= chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break
                current_chunk_sentences = overlap_sentences
                current_length = overlap_len

            current_chunk_sentences.append(sentence)
            current_length += sentence_len

        # Emit final chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append({
                "chunk_id": _create_chunk_id(
                    section_doc["document"], section_doc["section"], chunk_index
                ),
                "text": chunk_text,
                "document": section_doc["document"],
                "department": section_doc["department"],
                "policy_type": section_doc["policy_type"],
                "section": section_doc["section"],
                "page": section_doc["page"],
            })

    return chunks


def chunk_documents(
    sections: List[Dict[str, Any]],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Chunk all section-level documents.

    Args:
        sections: List of section-level dicts from metadata.enrich_metadata().
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap characters between chunks.

    Returns:
        List of chunk dicts ready for embedding.
    """
    all_chunks = []
    for section_doc in sections:
        chunks = chunk_section(section_doc, chunk_size, chunk_overlap)
        all_chunks.extend(chunks)

    logger.info(f"Created {len(all_chunks)} chunks from {len(sections)} sections")
    return all_chunks
