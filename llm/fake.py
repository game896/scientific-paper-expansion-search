import types
import typing
from typing import Any

from pydantic import BaseModel

from llm.interface import T


def _dummy(annotation: Any) -> Any:
    """Build a minimal valid value for any annotation, so the fake works with every schema."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin in (typing.Union, types.UnionType):
        return _dummy(next(a for a in args if a is not type(None)))
    if origin is list:
        return [_dummy(args[0])]
    if origin is dict:
        return {}
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.model_validate({name: _dummy(f.annotation) for name, f in annotation.model_fields.items()})
    return {str: "fake text", int: 0, float: 0.0, bool: False}.get(annotation)


class FakeLLM:
    """Returns a minimal valid object for any schema. For trying the plumbing without a key."""

    @property
    def model_name(self) -> str:
        return "fake"

    def generate(self, prompt: str, schema: type[T]) -> T:
        return _dummy(schema)
