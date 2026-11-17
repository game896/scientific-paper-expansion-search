from config import Settings
from sources.fake import FakeSource
from sources.interface import Source
from sources.openalex import OpenAlexSource


def create_source(settings: Settings) -> Source:
    if settings.source_provider == "openalex":
        return OpenAlexSource(email=settings.openalex_email)
    return FakeSource()
