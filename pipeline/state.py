import os
from pathlib import Path

from pydantic import BaseModel, ValidationError

from pipeline.errors import PipelineError


class EntityState(BaseModel):
    name: str
    paper_ids: list[str] = []


class State(BaseModel):
    """What the pipeline must remember between runs. Relations between entities are NOT stored in the
    vector store; this only tracks which accepted papers an author/journal appeared in, to decide
    when to create their profile and whom to crawl next."""

    last_run: str | None = None
    fetched_authors: list[str] = []
    authors: dict[str, EntityState] = {}
    journals: dict[str, EntityState] = {}


def load_state(path: Path) -> State:
    if not path.exists():
        return State()
    try:
        return State.model_validate_json(path.read_text(encoding="utf-8"))
    except (ValidationError, OSError) as exc:
        raise PipelineError(f"State file {path} is unreadable. Fix or delete it (a delete means re-fetching).") from exc


def save_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(state.model_dump_json(indent=1), encoding="utf-8")
    os.replace(tmp, path)
