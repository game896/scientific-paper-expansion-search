from typing import Protocol


class Embedder(Protocol):
    """Turns text into vectors. All entities must use the same embedder to share one space."""

    @property
    def model_name(self) -> str:
        """Identifies provider, model and size; stored with the data to catch accidental mixing."""
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...
