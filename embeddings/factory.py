from config import Settings
from embeddings.fake import FakeEmbedder
from embeddings.gemini import GeminiEmbedder
from embeddings.interface import Embedder


def create_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "gemini":
        return GeminiEmbedder(
            settings.gemini_api_key,
            settings.gemini_embedding_model,
            settings.embedding_dimensions,
            settings.embedding_texts_per_minute,
        )
    return FakeEmbedder(settings.embedding_dimensions)
