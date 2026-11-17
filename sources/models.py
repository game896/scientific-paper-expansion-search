from pydantic import BaseModel


class AuthorRef(BaseModel):
    source_id: str
    name: str


class JournalRef(BaseModel):
    source_id: str
    name: str


class Paper(BaseModel):
    source_id: str
    title: str
    abstract: str = ""
    year: int | None = None
    doi: str | None = None
    authors: list[AuthorRef] = []
    journal: JournalRef | None = None
    topics: list[str] = []


class AuthorMatch(BaseModel):
    """An author found by name, with enough detail for a person to check the match."""

    source_id: str
    name: str
    works_count: int = 0
    institution: str = ""
