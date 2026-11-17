import logging
import time

from google import genai
from google.genai import errors, types

from embeddings.errors import EmbeddingError
from embeddings.vectors import normalize
from gemini_common import RateLimiter, retry_wait

log = logging.getLogger(__name__)

BATCH_SIZE = 100
RETRIES = 6
RETRYABLE_CODES = {429, 500, 502, 503, 504}


class GeminiEmbedder:
    def __init__(self, api_key: str, model: str, dimensions: int, texts_per_minute: int) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._dimensions = dimensions
        self._limiter = RateLimiter(texts_per_minute)  # the free tier counts every text, not every request
        self._batch_size = min(BATCH_SIZE, texts_per_minute)

    @property
    def model_name(self) -> str:
        return f"gemini:{self._model}:{self._dimensions}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            vectors.extend(self._embed(texts[start : start + self._batch_size], "RETRIEVAL_DOCUMENT"))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        config = types.EmbedContentConfig(task_type=task_type, output_dimensionality=self._dimensions)
        for attempt in range(1, RETRIES + 1):
            self._limiter.acquire(len(texts))
            try:
                response = self._client.models.embed_content(model=self._model, contents=texts, config=config)
                break
            except errors.APIError as exc:
                wait = retry_wait(str(exc), attempt)
                log.warning("Gemini embedding failed (attempt %d/%d), waiting %.0fs: %s", attempt, RETRIES, wait, str(exc)[:200])
                if exc.code not in RETRYABLE_CODES or attempt == RETRIES:
                    raise EmbeddingError(f"Gemini embedding failed (HTTP {exc.code}). See the log for details.") from exc
                time.sleep(wait)
        vectors = [normalize(list(e.values)) for e in response.embeddings or []]
        if len(vectors) != len(texts):
            raise EmbeddingError(f"Gemini returned {len(vectors)} vectors for {len(texts)} texts.")
        return vectors
