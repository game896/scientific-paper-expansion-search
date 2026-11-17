import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from store.errors import StoreError
from store.models import EntityType, Hit, Item

log = logging.getLogger(__name__)

COLLECTION = "field"
MODEL_KEY = "embedding_model"


class ChromaStore:
    def __init__(self, path: Path, embedding_model: str) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(path), settings=ChromaSettings(anonymized_telemetry=False))
            self._collection = client.get_or_create_collection(
                COLLECTION, metadata={"hnsw:space": "cosine", MODEL_KEY: embedding_model}
            )
        except Exception as exc:
            log.exception("Could not open the Chroma store at %s", path)
            raise StoreError("Could not open the vector store. See the log for details.") from exc
        stored_model = (self._collection.metadata or {}).get(MODEL_KEY)
        if stored_model != embedding_model:
            raise StoreError(
                f"The store at {path} was built with embedding model '{stored_model}', "
                f"but the current one is '{embedding_model}'. Vectors from different models cannot be mixed: "
                "re-embed everything into a new store."
            )

    def upsert(self, items: list[Item]) -> None:
        if not items:
            return
        try:
            self._collection.upsert(
                ids=[i.id for i in items],
                embeddings=[i.vector for i in items],
                documents=[i.text for i in items],
                metadatas=[{**i.metadata, "type": i.type} for i in items],
            )
        except Exception as exc:
            log.exception("Chroma upsert failed")
            raise StoreError("Saving to the vector store failed. See the log for details.") from exc

    def search(self, vector: list[float], n: int = 10, type: EntityType | None = None) -> list[Hit]:
        try:
            result = self._collection.query(
                query_embeddings=[vector],
                n_results=n,
                where={"type": type} if type else None,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            log.exception("Chroma query failed")
            raise StoreError("Searching the vector store failed. See the log for details.") from exc
        hits = []
        for item_id, text, meta, distance in zip(
            result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            meta = dict(meta)
            hits.append(Hit(id=item_id, type=meta.pop("type"), text=text, metadata=meta, score=1.0 - distance))
        return hits

    def get(self, item_id: str) -> Item | None:
        try:
            result = self._collection.get(ids=[item_id], include=["documents", "metadatas", "embeddings"])
        except Exception as exc:
            log.exception("Chroma get failed")
            raise StoreError("Reading from the vector store failed. See the log for details.") from exc
        if not result["ids"]:
            return None
        meta = dict(result["metadatas"][0])
        return Item(
            id=item_id,
            type=meta.pop("type"),
            text=result["documents"][0],
            vector=[float(x) for x in result["embeddings"][0]],
            metadata=meta,
        )

    def existing_ids(self, ids: list[str]) -> set[str]:
        if not ids:
            return set()
        try:
            return set(self._collection.get(ids=ids, include=[])["ids"])
        except Exception as exc:
            log.exception("Chroma get failed")
            raise StoreError("Reading from the vector store failed. See the log for details.") from exc

    def count(self, type: EntityType | None = None) -> int:
        if type is None:
            return self._collection.count()
        return len(self._collection.get(where={"type": type}, include=[])["ids"])
