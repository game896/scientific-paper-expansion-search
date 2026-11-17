"""Collect papers for the field: python main.py <how many new papers at most>

Example:  python main.py 25
"""

import logging
import sys

from config import SeedError, SettingsError, load_seed, load_settings
from embeddings import EmbeddingError
from llm import LLMError
from pipeline import PipelineError, create_pipeline
from sources import SourceError
from store import StoreError

USAGE = (
    "Navedi koliko novih radova najviše treba prikupiti, na primer:\n"
    "    run 25        (ili: python main.py 25)"
)


def parse_limit(args: list[str]) -> int | None:
    if len(args) != 1 or not args[0].isdigit() or int(args[0]) < 1:
        return None
    return int(args[0])


def main() -> int:
    limit = parse_limit(sys.argv[1:])
    if limit is None:
        print(USAGE)
        return 1
    try:
        settings = load_settings()
        pipeline = create_pipeline(settings, load_seed(settings.seed_path))
    except (SettingsError, SeedError, StoreError) as exc:
        print(exc)
        return 1
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        report = pipeline.run(limit=limit)
    except (PipelineError, SourceError, EmbeddingError, LLMError, StoreError) as exc:
        print(f"Prikupljanje nije uspelo: {exc}")
        return 1
    print("\n" + report.summary())
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
