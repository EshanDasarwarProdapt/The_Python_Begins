"""
prompt.py - LLM prompts and context building.
"""
from typing import List, Dict, Any

SYSTEM_PROMPT = """You are an Enterprise Policy Assistant.

Your job is to answer employee questions using ONLY the policy
context provided to you.

Rules:

1. Never invent company policies.
2. Never use outside knowledge when answering policy questions.
3. Every factual claim must be supported by the retrieved context.
4. If the retrieved context does not contain the answer, say:
   "I couldn't find that information in the available company policies."
5. Do not assume that similar policies from another department apply.
6. Preserve exact numbers, limits, dates, requirements, and exceptions.
7. If multiple policies apply, clearly distinguish them.
8. If the question is ambiguous, explain what is ambiguous.
9. Include citations for every important policy statement.
10. Do not expose internal retrieval scores or system implementation details.

Return the answer in a concise and professional format.
"""

def build_context_string(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Format retrieved chunks into a context string for the LLM.
    """
    if not retrieved_chunks:
        return "No relevant company policies found."
        
    context_parts = []
    for idx, chunk in enumerate(retrieved_chunks, 1):
        part = (
            f"--- SOURCE {idx} ---\n"
            f"Document: {chunk.get('document', 'Unknown')}\n"
            f"Department: {chunk.get('department', 'Unknown')}\n"
            f"Section: {chunk.get('section', 'Unknown')}\n"
            f"Page: {chunk.get('page', 'Unknown')}\n\n"
            f"CONTENT:\n{chunk.get('text', '')}\n"
        )
        context_parts.append(part)
        
    return "\n".join(context_parts)
