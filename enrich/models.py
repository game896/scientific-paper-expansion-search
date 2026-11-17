import re

from pydantic import BaseModel, field_validator


class Concept(BaseModel):
    name: str
    definition: str

    @field_validator("name")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().lower()

    @property
    def id(self) -> str:
        return concept_id(self.name)

    @property
    def text(self) -> str:
        """What gets embedded for this concept."""
        return f"{self.name}: {self.definition}"


class ConceptList(BaseModel):
    concepts: list[Concept]


class Profile(BaseModel):
    profile: str


class Verdict(BaseModel):
    reason: str  # asked first so the model reasons before it decides
    relevant: bool


def concept_id(name: str) -> str:
    return "concept:" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
