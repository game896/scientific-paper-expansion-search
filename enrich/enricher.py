from enrich.models import Concept, ConceptList, Profile, Verdict
from enrich.prompts import author_profile_prompt, concepts_prompt, journal_profile_prompt, relevance_prompt
from llm import LLM
from sources.models import Paper

MAX_CONCEPTS = 6
MAX_PROFILE_PAPERS = 15


class Enricher:
    """Asks the LLM for concepts and profiles. Stateless: the pipeline decides when to call and what to cache."""

    def __init__(self, llm: LLM, field_name: str, field_description: str) -> None:
        self._llm = llm
        self._field = field_name
        self._description = field_description

    def is_relevant(self, paper: Paper) -> bool:
        """Second opinion for papers whose similarity score is in the grey zone."""
        return self._llm.generate(relevance_prompt(self._field, self._description, paper), Verdict).relevant

    def concepts_for(self, paper: Paper) -> list[Concept]:
        result = self._llm.generate(concepts_prompt(self._field, paper, MAX_CONCEPTS), ConceptList)
        unique: dict[str, Concept] = {}
        for concept in result.concepts:
            if concept.name and concept.name not in unique:
                unique[concept.name] = concept
        return list(unique.values())[:MAX_CONCEPTS]

    def author_profile(self, name: str, papers: list[Paper]) -> str:
        prompt = author_profile_prompt(self._field, name, papers[:MAX_PROFILE_PAPERS])
        return self._llm.generate(prompt, Profile).profile.strip()

    def journal_profile(self, name: str, papers: list[Paper]) -> str:
        prompt = journal_profile_prompt(self._field, name, papers[:MAX_PROFILE_PAPERS])
        return self._llm.generate(prompt, Profile).profile.strip()
