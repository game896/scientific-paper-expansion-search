from config import Settings
from store.chroma import ChromaStore
from store.interface import VectorStore


def create_store(settings: Settings, embedding_model: str) -> VectorStore:
    return ChromaStore(settings.chroma_path, embedding_model)
