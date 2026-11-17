from dataclasses import dataclass, field

NEAR_THRESHOLD_SAMPLE = 8
LANDSCAPE_SAMPLES = 24


@dataclass
class RunReport:
    threshold: float = 0.0
    floor: float = 0.0
    fetched: int = 0
    llm_judged: int = 0
    duplicates: int = 0
    accepted: int = 0
    seed_accepted: int = 0
    enrich_failures: int = 0
    source_errors: int = 0
    concepts_added: int = 0
    authors_added: int = 0
    journals_added: int = 0
    budget_exhausted: bool = False
    accepted_scores: list[tuple[str, float]] = field(default_factory=list)
    rejected_scores: list[tuple[str, float]] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Run finished (accept at {self.threshold:.2f}, reject below {self.floor:.2f})",
            f"  fetched {self.fetched} unique papers, {self.duplicates} already in the store",
            f"  accepted {self.accepted} ({self.seed_accepted} seed papers), rejected {len(self.rejected_scores)}, "
            f"{self.llm_judged} judged by the LLM",
            f"  new concepts {self.concepts_added}, authors {self.authors_added}, journals {self.journals_added}",
            f"  enrichment failures {self.enrich_failures}, source errors {self.source_errors}",
        ]
        if self.budget_exhausted:
            lines.append("  paper budget reached; the run stopped early")
        everything = sorted(self.accepted_scores + self.rejected_scores, key=lambda p: -p[1])
        if len(everything) > LANDSCAPE_SAMPLES:
            step = (len(everything) - 1) / (LANDSCAPE_SAMPLES - 1)
            lines.append("\nScore landscape (evenly spaced samples of all scored papers, best first):")
            lines += [f"  {everything[round(i * step)][1]:.3f}  {everything[round(i * step)][0][:90]}" for i in range(LANDSCAPE_SAMPLES)]
        if self.accepted_scores:
            lowest = sorted(self.accepted_scores, key=lambda p: p[1])[:NEAR_THRESHOLD_SAMPLE]
            lines.append("\nLowest-scoring ACCEPTED:")
            lines += [f"  {s:.3f}  {t[:90]}" for t, s in lowest]
        if self.rejected_scores:
            highest = sorted(self.rejected_scores, key=lambda p: -p[1])[:NEAR_THRESHOLD_SAMPLE]
            lines.append("\nHighest-scoring REJECTED:")
            lines += [f"  {s:.3f}  {t[:90]}" for t, s in highest]
        return "\n".join(lines)
