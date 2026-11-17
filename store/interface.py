from typing import Protocol

from store.models import EntityType, Hit, Item


class VectorStore(Protocol):
    """One shared vector space for all entity types. Implementations raise StoreError."""

    def upsert(self, items: list[Item]) -> None: ...

    def search(self, vector: list[float], n: int = 10, type: EntityType | None = None) -> list[Hit]: ...

    def get(self, item_id: str) -> Item | None: ...

    def existing_ids(self, ids: list[str]) -> set[str]: ...

    def count(self, type: EntityType | None = None) -> int: ...
