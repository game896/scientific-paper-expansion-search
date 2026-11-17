from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLM(Protocol):
    """A language model used as a plain function: a prompt in, a validated object out."""

    @property
    def model_name(self) -> str: ...

    def generate(self, prompt: str, schema: type[T]) -> T:
        """Return an instance of `schema`. Raises LLMError, never a provider exception."""
        ...
