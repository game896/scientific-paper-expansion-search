import logging
import time

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from llm.errors import LLMError
from gemini_common import retry_wait
from llm.interface import T

log = logging.getLogger(__name__)
logging.getLogger("google_genai").setLevel(logging.WARNING)  # its INFO lines repeat on every call

RETRIES = 6
RETRYABLE_CODES = {429, 500, 502, 503, 504}
TEMPERATURE = 0.2


class GeminiLLM:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @property
    def model_name(self) -> str:
        return f"gemini:{self._model}"

    def generate(self, prompt: str, schema: type[T]) -> T:
        config = types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=schema, temperature=TEMPERATURE
        )
        for attempt in range(1, RETRIES + 1):
            try:
                response = self._client.models.generate_content(model=self._model, contents=prompt, config=config)
                break
            except errors.APIError as exc:
                wait = retry_wait(str(exc), attempt)
                log.warning("Gemini generation failed (attempt %d/%d), waiting %.0fs: %s", attempt, RETRIES, wait, str(exc)[:200])
                if exc.code not in RETRYABLE_CODES or attempt == RETRIES:
                    raise LLMError(f"Gemini request failed (HTTP {exc.code}). See the log for details.") from exc
                time.sleep(wait)
        if not response.text:
            log.warning("Gemini returned no text (feedback: %s)", response.prompt_feedback)
            raise LLMError("Gemini returned an empty answer.")
        try:
            return schema.model_validate_json(response.text)
        except ValidationError as exc:
            log.warning("Gemini output did not match %s: %s", schema.__name__, response.text[:500])
            raise LLMError("Gemini returned an answer in an unexpected shape.") from exc
