"""ChromaDB client wrapper for vector database operations."""

import os

import chromadb


def _get_chroma_dir() -> str:
    """
    Get the ChromaDB data directory path.

    Notes:
        This is intentionally local to this module (it's the only consumer).
        Chroma data is stored under `.data/chroma` relative to the current
        working directory.
    """
    return os.path.join(os.getcwd(), ".data", "chroma")


def _init_chroma_client() -> chromadb.PersistentClient:
    chroma_path = _get_chroma_dir()
    os.makedirs(chroma_path, exist_ok=True)
    return chromadb.PersistentClient(path=chroma_path)


# Singleton Chroma client instance (import and use this everywhere).
client = _init_chroma_client()


