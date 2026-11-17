from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator


class SeedError(Exception):
    """Raised with a readable message when seed.yaml is missing or invalid."""


class FieldInfo(BaseModel):
    name: str
    description: str


class SeedPaper(BaseModel):
    title: str
    doi: str | None = None


class SeedAuthor(BaseModel):
    name: str
    openalex_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _from_plain_name(cls, value: object) -> object:
        return {"name": value} if isinstance(value, str) else value


class Seed(BaseModel):
    field: FieldInfo
    authors: list[SeedAuthor] = Field(min_length=1)
    papers: list[SeedPaper] = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)


def load_seed(path: Path) -> Seed:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SeedError(f"Seed file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise SeedError(f"Seed file {path} is not valid YAML: {exc}") from exc
    try:
        return Seed.model_validate(raw)
    except ValidationError as exc:
        lines = [f"- {'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        raise SeedError(f"Invalid seed file {path}:\n" + "\n".join(lines)) from exc
