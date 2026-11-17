from typing import Literal

from pydantic import BaseModel

EntityType = Literal["paper", "author", "concept", "journal"]
Metadata = dict[str, str | int | float | bool]


class Item(BaseModel):
    id: str
    type: EntityType
    text: str
    vector: list[float]
    metadata: Metadata = {}


class Hit(BaseModel):
    id: str
    type: EntityType
    text: str
    metadata: Metadata
    score: float  # cosine similarity, 1.0 = identical direction
