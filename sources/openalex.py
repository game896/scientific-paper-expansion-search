import logging
import time
import unicodedata

import httpx

from sources.errors import SourceError
from sources.models import AuthorMatch, AuthorRef, JournalRef, Paper

log = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org"
MAX_PAGE_SIZE = 200
RETRIES = 3
WORK_FIELDS = "id,doi,title,publication_year,abstract_inverted_index,authorships,primary_location,topics"


def _short_id(url: str | None) -> str:
    """OpenAlex ids come as full URLs; keep only the last part (e.g. W123)."""
    return (url or "").rsplit("/", 1)[-1]


def _abstract(inverted: dict[str, list[int]] | None) -> str:
    if not inverted:
        return ""
    positions = {pos: word for word, places in inverted.items() for pos in places}
    return " ".join(positions[i] for i in sorted(positions))


def _paper(raw: dict) -> Paper | None:
    title = raw.get("title")
    if not title:
        return None
    authors = [
        AuthorRef(source_id=_short_id(a["author"].get("id")), name=a["author"].get("display_name") or "")
        for a in raw.get("authorships") or []
        if a.get("author") and a["author"].get("id")
    ]
    venue = ((raw.get("primary_location") or {}).get("source")) or {}
    journal = JournalRef(source_id=_short_id(venue["id"]), name=venue.get("display_name") or "") if venue.get("id") else None
    doi = raw.get("doi")
    return Paper(
        source_id=_short_id(raw.get("id")),
        title=title,
        abstract=_abstract(raw.get("abstract_inverted_index")),
        year=raw.get("publication_year"),
        doi=doi.removeprefix("https://doi.org/") if doi else None,
        authors=authors,
        journal=journal,
        topics=[t["display_name"] for t in raw.get("topics") or [] if t.get("display_name")],
    )


def _normalize_name(name: str) -> str:
    """Lower case and unify the many Unicode hyphens OpenAlex uses (e.g. U+2010 in Eric-Jan)."""
    name = unicodedata.normalize("NFKC", name).lower()
    return "".join("-" if unicodedata.category(ch) == "Pd" else ch for ch in name)


def _author_match(raw: dict, fallback_name: str) -> AuthorMatch:
    institutions = raw.get("last_known_institutions") or []
    return AuthorMatch(
        source_id=_short_id(raw.get("id")),
        name=raw.get("display_name") or fallback_name,
        works_count=raw.get("works_count", 0),
        institution=institutions[0].get("display_name", "") if institutions else "",
    )


class OpenAlexSource:
    def __init__(self, email: str = "", client: httpx.Client | None = None) -> None:
        self._email = email
        self._client = client or httpx.Client(base_url=BASE_URL, timeout=30.0)

    def _get(self, path: str, params: dict) -> dict:
        if self._email:
            params = {**params, "mailto": self._email}
        for attempt in range(1, RETRIES + 1):
            try:
                response = self._client.get(path, params=params)
                if response.status_code == 429 or response.status_code >= 500:
                    raise httpx.HTTPStatusError("retryable", request=response.request, response=response)
                response.raise_for_status()
                return response.json()
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                log.warning("OpenAlex %s failed (attempt %d/%d): %s", path, attempt, RETRIES, exc)
                retryable = isinstance(exc, httpx.TransportError) or exc.response.status_code in (429, 500, 502, 503, 504)
                if not retryable or attempt == RETRIES:
                    raise SourceError("OpenAlex request failed. See the log for details.") from exc
                time.sleep(2**attempt)
        raise SourceError("OpenAlex request failed.")

    def _works(self, filters: str, search: str | None, since: str | None, limit: int, sort: str | None = None) -> list[Paper]:
        if since:
            filters = f"{filters},from_publication_date:{since}" if filters else f"from_publication_date:{since}"
        params: dict = {"per-page": min(limit, MAX_PAGE_SIZE), "select": WORK_FIELDS}
        if filters:
            params["filter"] = filters
        if search:
            params["search"] = search
        if sort:
            params["sort"] = sort
        data = self._get("/works", params)
        papers = [p for p in (_paper(raw) for raw in data.get("results", [])) if p]
        return papers[:limit]

    def find_paper_by_title(self, title: str) -> Paper | None:
        papers = self._works("", search=title, since=None, limit=1)
        return papers[0] if papers else None

    def find_author(self, name: str) -> AuthorMatch | None:
        data = self._get("/authors", {"search": name, "per-page": 5})
        results = data.get("results", [])
        if not results:
            return None
        wanted = _normalize_name(name)
        exact = [r for r in results if _normalize_name(r.get("display_name") or "") == wanted]
        best = max(exact or results[:1], key=lambda r: r.get("works_count", 0))
        return _author_match(best, fallback_name=name)

    def get_author(self, author_id: str) -> AuthorMatch | None:
        try:
            return _author_match(self._get(f"/authors/{author_id}", {}), fallback_name=author_id)
        except SourceError:
            return None

    def works_by_author(self, author_id: str, since: str | None = None, limit: int = 50) -> list[Paper]:
        return self._works(f"author.id:{author_id}", search=None, since=since, limit=limit, sort="cited_by_count:desc")

    def search_works(self, query: str, since: str | None = None, limit: int = 50) -> list[Paper]:
        return self._works("", search=query, since=since, limit=limit)
