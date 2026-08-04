"""RAG knowledge retriever tool for the TriPi agent."""

from __future__ import annotations

import os

from langchain_core.tools import tool


@tool
def knowledge_search(query: str) -> str:
    """Search the TriPi knowledge base for travel tips, safety info, packing guides, and destination advice.

    Uses ChromaDB vector store with Gemini embeddings for semantic retrieval.

    Args:
        query: Natural language search query (e.g. "what to pack for monsoon in Goa").

    Returns:
        Relevant knowledge passages or fallback message.
    """
    try:
        from rag.store import get_vector_store

        store = get_vector_store()
        results = store.similarity_search(query, k=3)

        if not results:
            return (
                "📚 No relevant information found in the knowledge base. "
                "The AI agent will use its built-in knowledge instead."
            )

        lines = ["📚 From the TriPi Knowledge Base:\n"]
        for i, doc in enumerate(results, 1):
            category = doc.metadata.get("category", "general")
            content = doc.page_content.strip()
            lines.append(f"  [{category}] {content}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return (
            f"Knowledge base search encountered an issue: {str(e)}. "
            "The AI agent will use its built-in knowledge instead."
        )
