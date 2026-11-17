import hashlib
import re

from embeddings.vectors import normalize


class FakeEmbedder:
    """Deterministic hashed bag-of-words vectors: texts sharing words are close. No network, no key."""

    def __init__(self, dimensions: int) -> None:
        self._dimensions = dimensions

    @property
    def model_name(self) -> str:
        return f"fake:{self._dimensions}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for word in re.findall(r"\w+", text.lower()):
            digest = hashlib.md5(word.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % self._dimensions] += 1.0 if digest[4] % 2 else -1.0
        return normalize(vector)
