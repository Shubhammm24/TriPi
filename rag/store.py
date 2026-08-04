"""ChromaDB vector store for the TriPi RAG knowledge base."""

from __future__ import annotations

import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings


_PERSIST_DIR = Path(__file__).resolve().parent / ".chroma"
_COLLECTION_NAME = "tripi_knowledge"


def get_embeddings(api_key: str | None = None) -> GoogleGenerativeAIEmbeddings:
    """Return a Gemini embeddings model instance."""
    key = api_key or os.getenv("GOOGLE_API_KEY", "")
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=key,
    )


def get_vector_store(api_key: str | None = None) -> Chroma:
    """Return a persistent ChromaDB vector store.

    Creates the store on first call; subsequent calls reuse persisted data.
    """
    embeddings = get_embeddings(api_key)
    return Chroma(
        collection_name=_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(_PERSIST_DIR),
    )
