from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsError(Exception):
    """Raised with a readable message when the configuration is invalid."""


class Settings(BaseSettings):
    # hide_input_in_errors: a validation error must never echo the values read from .env (the API key)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    gemini_api_key: str = ""

    llm_provider: Literal["gemini", "fake"] = "gemini"
    embedding_provider: Literal["gemini", "fake"] = "gemini"
    source_provider: Literal["openalex", "fake"] = "openalex"

    gemini_llm_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = Field(default=768, gt=0, le=3072)
    embedding_texts_per_minute: int = Field(default=90, gt=0)
    openalex_email: str = ""

    chroma_path: Path = Path("data/chroma")
    seed_path: Path = Path("seed.yaml")
    state_path: Path = Path("data/state.json")

    max_papers: int = Field(default=3000, gt=0)
    relevance_threshold: float = Field(default=0.80, ge=0.0, le=1.0)  # accepted without asking the LLM
    relevance_floor: float = Field(default=0.70, ge=0.0, le=1.0)  # rejected without asking the LLM

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @model_validator(mode="after")
    def _floor_below_threshold(self) -> "Settings":
        if self.relevance_floor > self.relevance_threshold:
            raise ValueError("RELEVANCE_FLOOR must not be higher than RELEVANCE_THRESHOLD")
        return self

    @property
    def needs_gemini_key(self) -> bool:
        return "gemini" in (self.llm_provider, self.embedding_provider)


def load_settings(require_gemini_key: bool = True) -> Settings:
    """Load settings; modules that never call Gemini (e.g. sources) pass require_gemini_key=False."""
    try:
        settings = Settings()
    except ValidationError as exc:
        lines = [f"- {'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        raise SettingsError("Invalid configuration:\n" + "\n".join(lines)) from exc
    if require_gemini_key and settings.needs_gemini_key and not settings.gemini_api_key.strip():
        raise SettingsError(
            "Invalid configuration:\n- gemini_api_key: GEMINI_API_KEY is empty but a provider is set to gemini. "
            "Set the key in .env or use LLM_PROVIDER=fake / EMBEDDING_PROVIDER=fake."
        )
    return settings
