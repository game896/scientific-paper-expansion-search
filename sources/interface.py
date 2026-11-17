from typing import Protocol

from sources.models import AuthorMatch, Paper


class Source(Protocol):
    """Where papers come from. Implementations raise SourceError, never provider exceptions."""

    def find_paper_by_title(self, title: str) -> Paper | None: ...

    def find_author(self, name: str) -> AuthorMatch | None: ...

    def get_author(self, author_id: str) -> AuthorMatch | None: ...

    def works_by_author(self, author_id: str, since: str | None = None, limit: int = 50) -> list[Paper]: ...

    def search_works(self, query: str, since: str | None = None, limit: int = 50) -> list[Paper]: ...
