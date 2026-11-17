from sources.models import AuthorMatch, AuthorRef, JournalRef, Paper

_AUTHOR = AuthorRef(source_id="A1", name="Fake Author")
_JOURNAL = JournalRef(source_id="S1", name="Journal of Fake Psychology")


def _paper(n: int, title: str) -> Paper:
    return Paper(
        source_id=f"W{n}",
        title=title,
        abstract=f"Abstract of '{title}'. A formal model of decision making and response time.",
        year=2000 + n,
        doi=f"10.0000/fake.{n}",
        authors=[_AUTHOR],
        journal=_JOURNAL,
        topics=["Decision making", "Response time"],
    )


class FakeSource:
    """Canned data so the pipeline can run without network access."""

    def find_paper_by_title(self, title: str) -> Paper | None:
        return _paper(1, title)

    def find_author(self, name: str) -> AuthorMatch | None:
        return AuthorMatch(source_id="A1", name=name, works_count=10, institution="Fake University")

    def get_author(self, author_id: str) -> AuthorMatch | None:
        return AuthorMatch(source_id=author_id, name="Fake Author", works_count=10, institution="Fake University")

    def works_by_author(self, author_id: str, since: str | None = None, limit: int = 50) -> list[Paper]:
        return [_paper(n, f"Fake paper {n} by {author_id}") for n in range(2, min(limit, 4) + 2)]

    def search_works(self, query: str, since: str | None = None, limit: int = 50) -> list[Paper]:
        return [_paper(n, f"Fake paper {n} about {query}") for n in range(5, min(limit, 3) + 5)]
