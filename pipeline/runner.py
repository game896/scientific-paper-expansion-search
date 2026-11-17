import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from config import Seed, Settings
from embeddings import Embedder
from enrich import Enricher
from llm import LLMError
from pipeline.relevance import RelevanceFilter
from pipeline.report import RunReport
from pipeline.state import EntityState, State, load_state, save_state
from sources import Paper, Source, SourceError
from store import Item, VectorStore

log = logging.getLogger(__name__)

AUTHOR_WORKS_LIMIT = 50
KEYWORD_LIMIT = 50
EXPANSION_MIN_PAPERS = 3  # an author with this many accepted papers becomes a crawl target
EXPANSION_AUTHORS_PER_RUN = 20
MIN_AUTHOR_PAPERS = 2  # authors seen less often get no profile (seed authors always do)
MIN_JOURNAL_PAPERS = 3
PROGRESS_EVERY = 25


def paper_item_id(paper: Paper) -> str:
    return f"paper:{paper.source_id}"


def _today() -> str:
    return date.today().isoformat()


def _paper_text(paper: Paper) -> str:
    return f"{paper.title}\n\n{paper.abstract}" if paper.abstract else paper.title


@dataclass
class _Run:
    state: State
    report: RunReport
    relevance: RelevanceFilter
    budget: int
    since: str | None
    seed_author_ids: set[str] = field(default_factory=set)
    seen: set[str] = field(default_factory=set)


class Pipeline:
    def __init__(
        self,
        settings: Settings,
        seed: Seed,
        source: Source,
        embedder: Embedder,
        store: VectorStore,
        enricher: Enricher,
        state_path: Path,
    ) -> None:
        self._settings = settings
        self._seed = seed
        self._source = source
        self._embedder = embedder
        self._store = store
        self._enricher = enricher
        self._state_path = state_path

    def run(self, limit: int | None = None) -> RunReport:
        threshold = self._settings.relevance_threshold
        floor = self._settings.relevance_floor
        field_vector = self._embedder.embed_documents([self._seed.field.description])[0]
        room = self._settings.max_papers - self._store.count("paper")
        state = load_state(self._state_path)
        ctx = _Run(
            state=state,
            report=RunReport(threshold=threshold, floor=floor),
            relevance=RelevanceFilter(field_vector, threshold, floor),
            budget=max(0, min(room, limit) if limit else room),
            since=state.last_run,
        )
        try:
            self._collect_seed(ctx)
            self._expand(ctx)
            self._build_entities(ctx)
        finally:
            if ctx.budget > 0:  # only a complete run may move the "since" date forward
                state.last_run = date.today().isoformat()
            save_state(self._state_path, state)
        ctx.report.budget_exhausted = ctx.budget <= 0
        return ctx.report

    # ---- collecting candidates -------------------------------------------------

    def _collect_seed(self, ctx: _Run) -> None:
        for seed_paper in self._seed.papers:
            if ctx.budget <= 0:
                return
            paper = self._guarded(ctx, lambda: self._source.find_paper_by_title(seed_paper.title))
            if paper:
                self._ingest(ctx, [paper], exempt=True)
        for author in self._seed.authors:
            if ctx.budget <= 0:
                return
            author_id = author.openalex_id
            if author_id is None:
                match = self._guarded(ctx, lambda: self._source.find_author(author.name))
                author_id = match.source_id if match else None
            if author_id is None:
                log.warning("Seed author %s was not found", author.name)
                continue
            ctx.seed_author_ids.add(author_id)
            self._fetch_author(ctx, author_id)
        for keyword in self._seed.keywords:
            if ctx.budget <= 0:
                return
            papers = self._guarded(ctx, lambda: self._source.search_works(keyword, ctx.since, KEYWORD_LIMIT))
            if papers:
                log.info("Keyword '%s': %d candidates", keyword, len(papers))
                self._ingest(ctx, papers)

    def _expand(self, ctx: _Run) -> None:
        """Crawl authors who showed up in several accepted papers: this is the autonomous growth."""
        fetched = set(ctx.state.fetched_authors)
        targets = sorted(
            (a for a, e in ctx.state.authors.items() if len(e.paper_ids) >= EXPANSION_MIN_PAPERS and a not in fetched),
            key=lambda a: -len(ctx.state.authors[a].paper_ids),
        )[:EXPANSION_AUTHORS_PER_RUN]
        for author_id in targets:
            if ctx.budget <= 0:
                return
            log.info("Expanding to author %s (%s)", ctx.state.authors[author_id].name, author_id)
            self._fetch_author(ctx, author_id)

    def _fetch_author(self, ctx: _Run, author_id: str) -> None:
        papers = self._guarded(ctx, lambda: self._source.works_by_author(author_id, ctx.since, AUTHOR_WORKS_LIMIT))
        if papers is None:
            return
        log.info("Author %s: %d candidates", author_id, len(papers))
        self._ingest(ctx, papers)
        if author_id not in ctx.state.fetched_authors:
            ctx.state.fetched_authors.append(author_id)

    def _guarded(self, ctx: _Run, call):
        try:
            return call()
        except SourceError as exc:
            log.warning("Source error, skipping: %s", exc)
            ctx.report.source_errors += 1
            return None

    # ---- filter and store ---------------------------------------------------------

    def _ingest(self, ctx: _Run, papers: list[Paper], exempt: bool = False) -> None:
        report = ctx.report
        unique = [p for p in papers if paper_item_id(p) not in ctx.seen]
        ctx.seen.update(paper_item_id(p) for p in unique)
        report.fetched += len(unique)
        known = self._store.existing_ids([paper_item_id(p) for p in unique])
        fresh = [p for p in unique if paper_item_id(p) not in known]
        report.duplicates += len(unique) - len(fresh)
        if not fresh:
            return
        vectors = self._embedder.embed_documents([_paper_text(p) for p in fresh])
        for paper, vector in zip(fresh, vectors):
            if ctx.budget <= 0:
                return
            score = ctx.relevance.score(vector)
            decision = "accept" if exempt else ctx.relevance.decide(score)
            if decision == "ask":
                try:
                    decision = "accept" if self._enricher.is_relevant(paper) else "reject"
                except LLMError as exc:
                    log.warning("No relevance verdict for '%s' (will retry next run): %s", paper.title[:60], exc)
                    report.enrich_failures += 1
                    continue
                report.llm_judged += 1
            if decision == "reject":
                report.rejected_scores.append((paper.title, score))
                continue
            try:
                concepts = self._enricher.concepts_for(paper)
            except LLMError as exc:
                log.warning("Skipping '%s' (will retry next run): %s", paper.title[:60], exc)
                report.enrich_failures += 1
                continue
            self._store_paper(ctx, paper, vector, score, exempt, concepts)
            report.accepted += 1
            report.seed_accepted += int(exempt)
            report.accepted_scores.append((paper.title, score))
            ctx.budget -= 1
            if report.accepted % PROGRESS_EVERY == 0:
                log.info("Accepted %d papers so far", report.accepted)

    def _store_paper(self, ctx: _Run, paper: Paper, vector: list[float], score: float, seed: bool, concepts) -> None:
        pid = paper_item_id(paper)
        new_concepts = []
        known = self._store.existing_ids([c.id for c in concepts])
        for concept in concepts:
            if concept.id not in known:
                new_concepts.append(concept)
                known.add(concept.id)
        items = [
            Item(id=pid, type="paper", text=_paper_text(paper), vector=vector, metadata=_paper_metadata(paper, score, seed, concepts))
        ]
        if new_concepts:
            concept_vectors = self._embedder.embed_documents([c.text for c in new_concepts])
            items += [
                Item(id=c.id, type="concept", text=c.text, vector=v, metadata={"name": c.name, "first_seen": _today()})
                for c, v in zip(new_concepts, concept_vectors)
            ]
        self._store.upsert(items)
        ctx.report.concepts_added += len(new_concepts)
        for ref in paper.authors:
            ctx.state.authors.setdefault(ref.source_id, EntityState(name=ref.name)).paper_ids.append(pid)
        if paper.journal:
            ctx.state.journals.setdefault(paper.journal.source_id, EntityState(name=paper.journal.name)).paper_ids.append(pid)

    # ---- authors and journals -----------------------------------------------------

    def _build_entities(self, ctx: _Run) -> None:
        state = ctx.state
        authors = {
            a: e for a, e in state.authors.items() if len(e.paper_ids) >= MIN_AUTHOR_PAPERS or a in ctx.seed_author_ids
        }
        journals = {j: e for j, e in state.journals.items() if len(e.paper_ids) >= MIN_JOURNAL_PAPERS}
        ctx.report.authors_added = self._add_profiles(authors, "author", self._enricher.author_profile, ctx)
        ctx.report.journals_added = self._add_profiles(journals, "journal", self._enricher.journal_profile, ctx)

    def _add_profiles(self, entities: dict[str, EntityState], kind, make_profile, ctx: _Run) -> int:
        ids = {f"{kind}:{key}": key for key in entities}
        known = self._store.existing_ids(list(ids))
        added = 0
        for item_id, key in ids.items():
            if item_id in known:
                continue
            entity = entities[key]
            papers = self._stored_papers(entity.paper_ids)
            if not papers:
                continue
            try:
                profile = make_profile(entity.name, papers)
            except LLMError as exc:
                log.warning("No profile for %s '%s' this run: %s", kind, entity.name, exc)
                ctx.report.enrich_failures += 1
                continue
            vector = self._embedder.embed_documents([profile])[0]
            self._store.upsert(
                [
                    Item(
                        id=item_id,
                        type=kind,
                        text=profile,
                        vector=vector,
                        metadata={"name": entity.name, "papers": len(entity.paper_ids), "first_seen": _today()},
                    )
                ]
            )
            added += 1
        return added

    def _stored_papers(self, paper_ids: list[str]) -> list[Paper]:
        papers = []
        for pid in paper_ids:
            item = self._store.get(pid)
            if item is None:
                continue
            title = str(item.metadata.get("title", ""))
            abstract = item.text.split("\n\n", 1)[1] if "\n\n" in item.text else ""
            year = item.metadata.get("year")
            papers.append(Paper(source_id=pid.removeprefix("paper:"), title=title, abstract=abstract, year=int(year) if year else None))
        return papers


def _paper_metadata(paper: Paper, score: float, seed: bool, concepts) -> dict:
    meta: dict = {
        "title": paper.title,
        "relevance": round(score, 4),
        "seed": seed,
        "has_abstract": bool(paper.abstract),
        "first_seen": _today(),
        "authors": "; ".join(a.name for a in paper.authors),
        "concepts": "; ".join(c.name for c in concepts),
    }
    if paper.year:
        meta["year"] = paper.year
    if paper.doi:
        meta["doi"] = paper.doi
    if paper.journal:
        meta["journal"] = paper.journal.name
    return meta
