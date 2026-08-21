"""
pdf_loader.py - Extract text and metadata from PDF files using PyMuPDF.
"""
import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def load_pdf(filepath: str) -> List[Dict[str, Any]]:
    """
    Load a single PDF and return a list of page-level documents.

    Each document dict contains:
        - text: str (full page text)
        - page: int (1-indexed page number)
        - document: str (filename)
        - filepath: str (absolute path)

    Args:
        filepath: Absolute path to the PDF file.

    Returns:
        List of page-level document dicts.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"PDF not found: {filepath}")

    filename = os.path.basename(filepath)
    pages = []

    try:
        doc = fitz.open(filepath)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text").strip()
            if text:
                pages.append({
                    "text": text,
                    "page": page_num + 1,
                    "document": filename,
                    "filepath": filepath,
                })
        doc.close()
        logger.info(f"Loaded {len(pages)} pages from {filename}")
    except Exception as e:
        logger.error(f"Error loading PDF {filepath}: {e}")
        raise

    return pages


def load_all_pdfs(directory: str) -> List[Dict[str, Any]]:
    """
    Load all PDF files from a directory.

    Args:
        directory: Path to directory containing PDF files.

    Returns:
        Combined list of page-level document dicts from all PDFs.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    all_pages = []
    pdf_files = sorted([f for f in os.listdir(directory) if f.lower().endswith(".pdf")])

    if not pdf_files:
        logger.warning(f"No PDF files found in {directory}")
        return all_pages

    for pdf_file in pdf_files:
        filepath = os.path.join(directory, pdf_file)
        try:
            pages = load_pdf(filepath)
            all_pages.extend(pages)
        except Exception as e:
            logger.error(f"Skipping {pdf_file}: {e}")

    logger.info(f"Total pages loaded: {len(all_pages)} from {len(pdf_files)} PDFs")
    return all_pages
