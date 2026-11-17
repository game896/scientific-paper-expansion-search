from typing import Literal

from embeddings import cosine

Decision = Literal["accept", "reject", "ask"]


class RelevanceFilter:
    """Judges a candidate by its closeness to the field description in the shared vector space.

    Gemini embeddings give high scores to everything (unrelated text still scores about 0.65), so
    one threshold is not enough: at or above `accept_at` it is accepted, below `reject_below` it is
    rejected, and in between the caller must ask the LLM.
    """

    def __init__(self, field_vector: list[float], accept_at: float, reject_below: float) -> None:
        self._field_vector = field_vector
        self.accept_at = accept_at
        self.reject_below = reject_below

    def score(self, vector: list[float]) -> float:
        return cosine(self._field_vector, vector)

    def decide(self, score: float) -> Decision:
        if score >= self.accept_at:
            return "accept"
        return "reject" if score < self.reject_below else "ask"
