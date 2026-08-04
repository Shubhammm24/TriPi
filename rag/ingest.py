"""Document ingestion pipeline for the TriPi knowledge base.

Usage:
    python -m rag.ingest
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.store import get_vector_store


DATA_DIR = Path(__file__).resolve().parent / "data"


def ingest_documents(api_key: str | None = None) -> int:
    """Load markdown docs from ``rag/data/``, split, embed, and upsert.

    Returns the number of chunks ingested.
    """
    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        return 0

    loader = DirectoryLoader(
        str(DATA_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()

    if not documents:
        print("No markdown documents found in rag/data/")
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)

    # Add metadata
    for chunk in chunks:
        source = chunk.metadata.get("source", "")
        filename = Path(source).stem if source else "unknown"
        chunk.metadata["category"] = filename

    store = get_vector_store(api_key)
    store.add_documents(chunks)

    print(f"Ingested {len(chunks)} chunks from {len(documents)} documents.")
    return len(chunks)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    ingest_documents()
