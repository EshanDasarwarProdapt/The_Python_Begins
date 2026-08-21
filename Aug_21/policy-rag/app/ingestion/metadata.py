"""
metadata.py - Extract and enrich metadata from parsed PDF documents.
"""
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Mapping from filename patterns to department metadata
DEPARTMENT_MAP = {
    "finance": {
        "department": "Finance",
        "policy_type": "Financial Policy",
    },
    "hr": {
        "department": "HR",
        "policy_type": "Human Resources Policy",
    },
    "it_security": {
        "department": "IT Security",
        "policy_type": "IT Security Policy",
    },
    "it security": {
        "department": "IT Security",
        "policy_type": "IT Security Policy",
    },
    "legal": {
        "department": "Legal Compliance",
        "policy_type": "Legal Compliance Policy",
    },
}


def detect_department(document_name: str) -> Dict[str, str]:
    """
    Detect the department from the document filename.

    Args:
        document_name: The PDF filename.

    Returns:
        Dict with 'department' and 'policy_type' keys.
    """
    name_lower = document_name.lower().replace("_", " ").replace("-", " ")

    for key, meta in DEPARTMENT_MAP.items():
        if key in name_lower:
            return meta

    return {"department": "General", "policy_type": "General Policy"}


def extract_sections(text: str) -> List[Dict[str, str]]:
    """
    Split page text into sections based on heading patterns.

    Looks for lines that appear to be section headings:
    - Lines that are short, title-cased, and followed by content
    - Lines ending with a colon
    - Numbered sections (e.g., '1. Overview', '2.1 Scope')

    Args:
        text: Full page text.

    Returns:
        List of dicts with 'section' and 'text' keys.
    """
    lines = text.split("\n")
    sections = []
    current_section = "General"
    current_text_lines = []

    heading_pattern = re.compile(
        r"^(?:\d+\.?\s*)?([A-Z][A-Za-z\s/&,\-]{2,50})(?::?\s*)$"
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        match = heading_pattern.match(stripped)
        # A heading must be short (< 60 chars) and not look like a sentence
        is_heading = (
            match
            and len(stripped) < 60
            and not stripped.endswith(".")
            and stripped.count(" ") < 8
        )

        if is_heading:
            # Save previous section
            if current_text_lines:
                sections.append({
                    "section": current_section,
                    "text": "\n".join(current_text_lines).strip(),
                })
                current_text_lines = []
            current_section = stripped.rstrip(":").strip()
        else:
            current_text_lines.append(stripped)

    # Save last section
    if current_text_lines:
        sections.append({
            "section": current_section,
            "text": "\n".join(current_text_lines).strip(),
        })

    if not sections:
        sections.append({"section": "General", "text": text.strip()})

    return sections


def enrich_metadata(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich page-level documents with department metadata and section extraction.

    Args:
        pages: List of page-level dicts from pdf_loader.

    Returns:
        List of section-level dicts with enriched metadata.
    """
    enriched = []

    for page in pages:
        dept_meta = detect_department(page["document"])
        sections = extract_sections(page["text"])

        for section in sections:
            enriched.append({
                "text": section["text"],
                "document": page["document"],
                "department": dept_meta["department"],
                "policy_type": dept_meta["policy_type"],
                "section": section["section"],
                "page": page["page"],
            })

    logger.info(f"Enriched {len(pages)} pages into {len(enriched)} sections")
    return enriched
