from config import Seed, Settings
from embeddings import create_embedder
from enrich import Enricher
from llm import create_llm
from pipeline.runner import Pipeline
from sources import create_source
from store import create_store


def create_pipeline(settings: Settings, seed: Seed) -> Pipeline:
    embedder = create_embedder(settings)
    return Pipeline(
        settings=settings,
        seed=seed,
        source=create_source(settings),
        embedder=embedder,
        store=create_store(settings, embedder.model_name),
        enricher=Enricher(create_llm(settings), seed.field.name, seed.field.description),
        state_path=settings.state_path,
    )
