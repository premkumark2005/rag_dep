import json
import re
from typing import Protocol

from backend.config import Settings
from backend.utils.exceptions import (
    LLMConfigurationError,
    LLMGenerationError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient(Protocol):
    """Generic LLM interface."""

    def generate(self, prompt: str) -> str: ...


class MockLLMClient:
    """Offline-safe baseline generator for development and testing."""

    INSUFFICIENT_MESSAGE = "Insufficient information in the provided knowledge base."
    _STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }

    def generate(self, prompt: str) -> str:
        try:
            if "Return strict JSON only with this schema keys exactly" in prompt:
                return self._generate_plan_json(prompt)

            question_match = re.search(r"QUESTION:\s*(.*?)\s*CONTEXT:", prompt, flags=re.DOTALL)
            context_match = re.search(
                r"CONTEXT:\s*(.*?)\s*(?:INITIAL ANSWER:|ANSWER:)",
                prompt,
                flags=re.DOTALL,
            )

            question = question_match.group(1).strip() if question_match else ""
            context = context_match.group(1).strip() if context_match else ""

            if not context:
                return self.INSUFFICIENT_MESSAGE

            best_sentence = self._extract_best_sentence(question, context)
            return best_sentence or self.INSUFFICIENT_MESSAGE
        except Exception as exc:  # noqa: BLE001
            raise LLMGenerationError(f"Mock LLM generation failed: {exc}") from exc

    def _generate_plan_json(self, prompt: str) -> str:
        question_match = re.search(r"QUESTION:\s*(.*?)\s*EVIDENCE:", prompt, flags=re.DOTALL)
        question = question_match.group(1).strip() if question_match else ""
        evidence_entries = self._parse_planner_evidence(prompt)

        requirements = self._infer_requirements(question)
        required_facts: list[dict[str, object]] = []
        missing_facts: list[str] = []
        conflicting_facts: list[str] = []

        for index, requirement in enumerate(requirements, start=1):
            req_terms = self._tokenize(requirement)
            matches = []
            for item in evidence_entries:
                text = item["text"]
                if req_terms & self._tokenize(text):
                    matches.append(item)

            status = "FOUND"
            if not matches:
                status = "MISSING"
                missing_facts.append(requirement)
            else:
                lower_req = requirement.lower()
                if "when" in lower_req or "year" in lower_req or "date" in lower_req:
                    years = self._extract_years([entry["text"] for entry in matches])
                    if len(years) > 1:
                        status = "CONFLICTING"
                        conflicting_facts.append(requirement)
                    elif len(years) == 0:
                        status = "MISSING"
                        missing_facts.append(requirement)

            required_facts.append(
                {
                    "fact_id": f"fact_{index}",
                    "requirement": requirement,
                    "status": status,
                    "evidence": [
                        {
                            "chunk_id": entry["chunk_id"],
                            "document_id": entry["document_id"],
                            "supported_fact": entry["text"],
                        }
                        for entry in matches
                    ],
                }
            )

        if missing_facts or conflicting_facts:
            answer_instruction = (
                "Answer only using FOUND facts. Clearly state missing/conflicting information and avoid "
                "unsupported claims."
            )
        else:
            answer_instruction = "Answer using only the cited evidence for each required fact."

        payload = {
            "question_intent": f"Answer the question using evidence-grounded facts: {question}",
            "required_facts": required_facts,
            "missing_facts": missing_facts,
            "conflicting_facts": conflicting_facts,
            "answer_instruction": answer_instruction,
        }

        return json.dumps(payload)

    def _parse_planner_evidence(self, prompt: str) -> list[dict[str, str]]:
        matches = re.findall(
            r"- chunk_id:\s*(.+?)\n\s*document_id:\s*(.+?)\n\s*source:\s*(.+?)\n\s*text:\s*(.+?)(?=\n- chunk_id:|\Z)",
            prompt,
            flags=re.DOTALL,
        )
        entries: list[dict[str, str]] = []
        for chunk_id, document_id, _, text in matches:
            clean_text = text.strip()
            sentence = re.split(r"(?<=[.!?])\s+", clean_text)[0].strip() if clean_text else ""
            entries.append(
                {
                    "chunk_id": chunk_id.strip(),
                    "document_id": document_id.strip(),
                    "text": sentence or clean_text,
                }
            )
        return entries

    def _infer_requirements(self, question: str) -> list[str]:
        normalized = question.strip().rstrip("?")
        parts = [part.strip() for part in re.split(r"\band\b", normalized, flags=re.IGNORECASE) if part.strip()]
        return parts or [normalized]

    def _extract_years(self, sentences: list[str]) -> set[str]:
        years: set[str] = set()
        for sentence in sentences:
            years.update(re.findall(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", sentence))
        return years

    def _extract_best_sentence(self, question: str, context: str) -> str:
        cleaned_context = re.sub(r"\[Evidence\s+\d+\]", " ", context)
        cleaned_context = re.sub(r"Source:\s*[^\n]+", " ", cleaned_context)

        question_terms = self._tokenize(question)
        sentences = re.split(r"(?<=[.!?])\s+", cleaned_context.replace("\n", " "))

        best_score = 0
        best_sentence = ""
        for sentence in sentences:
            clean = sentence.strip()
            if not clean or clean.lower().startswith("source:"):
                continue
            sentence_terms = self._tokenize(clean)
            overlap = len(question_terms & sentence_terms)
            if overlap > best_score:
                best_score = overlap
                best_sentence = clean

        return best_sentence if best_score > 0 else ""

    def _tokenize(self, text: str) -> set[str]:
        tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
        return {token for token in tokens if token not in self._STOP_WORDS}


class GeminiLLMClient:
    """Google Gemini production client using the latest google-genai SDK."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        if not api_key or not api_key.strip():
            raise LLMConfigurationError("Gemini LLM provider requires a valid non-empty LLM_API_KEY.")
        self.api_key = api_key.strip()
        self.model_name = model_name or "gemini-2.5-flash"
        try:
            import httpx
            from google import genai
            from google.genai import types

            # Request timeout of 30 seconds with custom httpx client to ensure reliable TLS handshakes
            custom_httpx = httpx.Client(verify=False, timeout=30.0)
            http_options = types.HttpOptions(httpxClient=custom_httpx)
            self.client = genai.Client(api_key=self.api_key, http_options=http_options)
        except Exception as exc:
            raise LLMConfigurationError(f"Failed to initialize Google GenAI SDK: {exc}") from exc

    def generate(self, prompt: str) -> str:
        import time
        from google.genai.errors import APIError
        import httpx

        max_retries = 3
        backoff_sec = 1.0
        backoff_factor = 2.0

        logger.info("Gemini request started")

        for attempt in range(1, max_retries + 2):
            logger.info("Gemini call attempt %d of %d", attempt, max_retries + 1)
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                if not response.text:
                    if hasattr(response, "candidates") and response.candidates:
                        finish_reason = getattr(response.candidates[0], "finish_reason", "UNKNOWN")
                        raise LLMGenerationError(f"Gemini generation returned empty response. Finish reason: {finish_reason}")
                    raise LLMGenerationError("Gemini generation returned empty text response.")
                return response.text.strip()
            except Exception as exc:
                err_msg = str(exc)
                status_code = None
                if isinstance(exc, APIError):
                    status_code = exc.code

                is_retryable = False
                is_timeout = isinstance(exc, (httpx.TimeoutException, TimeoutError)) or "TIMEOUT" in err_msg.upper()

                if status_code is not None:
                    if status_code == 429 or status_code == 503 or status_code >= 500:
                        is_retryable = True
                elif is_timeout:
                    is_retryable = True
                elif "503" in err_msg or "429" in err_msg or "SERVICE_UNAVAILABLE" in err_msg.upper() or "RESOURCE_EXHAUSTED" in err_msg.upper():
                    is_retryable = True
                elif isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
                    is_retryable = True

                status_desc = f"status_code={status_code}" if status_code else "network/timeout/other"
                
                if is_retryable and attempt <= max_retries:
                    logger.warning(
                        "Gemini call attempt %d failed | %s | error: %s | retrying in %.2f seconds...",
                        attempt, status_desc, err_msg, backoff_sec
                    )
                    time.sleep(backoff_sec)
                    backoff_sec *= backoff_factor
                else:
                    logger.error(
                        "Gemini call final failure on attempt %d | %s | error: %s",
                        attempt, status_desc, err_msg
                    )
                    # Specific exceptions for 429 and 503 errors
                    if status_code == 429 or "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg.upper():
                        raise LLMRateLimitError(f"Gemini API rate limit exceeded: {exc}") from exc
                    if status_code == 503 or "503" in err_msg or "SERVICE_UNAVAILABLE" in err_msg.upper():
                        raise LLMServiceUnavailableError(f"Gemini API service unavailable: {exc}") from exc

                    if "API_KEY" in err_msg.upper() or "UNAUTHENTICATED" in err_msg.upper() or status_code in (401, 403):
                        raise LLMGenerationError(f"Gemini API authentication failed (invalid API key): {exc}") from exc
                    if "SAFETY" in err_msg.upper() or "BLOCKED" in err_msg.upper():
                        raise LLMGenerationError(f"Gemini generation blocked by safety settings: {exc}") from exc

                    raise LLMGenerationError(f"Gemini LLM generation failed after {attempt} attempts: {exc}") from exc



class GroqLLMClient:
    """Groq production client using the official groq Python SDK."""

    def __init__(self, api_key: str, model_name: str = "openai/gpt-oss-20b") -> None:
        if not api_key or not api_key.strip():
            raise LLMConfigurationError("Groq LLM provider requires a valid non-empty LLM_API_KEY.")
        self.api_key = api_key.strip()
        self.model_name = model_name or "openai/gpt-oss-20b"
        try:
            from groq import Groq

            self.client = Groq(api_key=self.api_key)
            logger.info("Groq client initialized | model=%s", self.model_name)
        except ImportError as exc:
            raise LLMConfigurationError(
                "The 'groq' package is not installed. Run: pip install groq"
            ) from exc
        except Exception as exc:
            raise LLMConfigurationError(f"Failed to initialize Groq client: {exc}") from exc

    def generate(self, prompt: str) -> str:
        import time

        max_retries = 3
        backoff_sec = 1.0
        backoff_factor = 2.0

        logger.info("Groq request started | model=%s", self.model_name)

        for attempt in range(1, max_retries + 2):
            logger.info("Groq call attempt %d of %d", attempt, max_retries + 1)
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30,
                )
                text = completion.choices[0].message.content
                if not text or not text.strip():
                    raise LLMGenerationError("Groq generation returned empty text response.")
                logger.info("Groq call succeeded on attempt %d", attempt)
                return text.strip()

            except LLMGenerationError:
                raise
            except Exception as exc:
                err_msg = str(exc)
                status_code = getattr(exc, "status_code", None)

                is_retryable = False
                if status_code in (429, 503) or (status_code is not None and status_code >= 500):
                    is_retryable = True
                elif any(code in err_msg for code in ("429", "503", "500")):
                    is_retryable = True
                elif "rate limit" in err_msg.lower() or "service unavailable" in err_msg.lower():
                    is_retryable = True
                elif "timeout" in err_msg.lower() or "connection" in err_msg.lower():
                    is_retryable = True

                status_desc = f"status_code={status_code}" if status_code else "network/timeout/other"

                if is_retryable and attempt <= max_retries:
                    logger.warning(
                        "Groq call attempt %d failed | %s | error: %s | retrying in %.2f seconds...",
                        attempt, status_desc, err_msg, backoff_sec,
                    )
                    time.sleep(backoff_sec)
                    backoff_sec *= backoff_factor
                else:
                    logger.error(
                        "Groq call final failure on attempt %d | %s | error: %s",
                        attempt, status_desc, err_msg,
                    )
                    if status_code == 429 or "rate limit" in err_msg.lower():
                        raise LLMRateLimitError(f"Groq API rate limit exceeded: {exc}") from exc
                    if status_code == 503 or "service unavailable" in err_msg.lower():
                        raise LLMServiceUnavailableError(f"Groq API service unavailable: {exc}") from exc
                    if status_code in (401, 403) or "authentication" in err_msg.lower() or "api_key" in err_msg.lower():
                        raise LLMConfigurationError(f"Groq API authentication failed (invalid API key): {exc}") from exc
                    raise LLMGenerationError(
                        f"Groq LLM generation failed after {attempt} attempts: {exc}"
                    ) from exc


def create_llm_client(settings: Settings) -> LLMClient:
    """Create an LLM client from environment configuration."""
    provider = settings.llm_provider.strip().lower()
    if provider == "mock":
        return MockLLMClient()

    if provider == "gemini":
        if not settings.llm_api_key:
            raise LLMConfigurationError("LLM_PROVIDER 'gemini' requires LLM_API_KEY to be set.")
        return GeminiLLMClient(
            api_key=settings.llm_api_key,
            model_name=settings.llm_model,
        )

    if provider == "groq":
        if not settings.llm_api_key:
            raise LLMConfigurationError("LLM_PROVIDER 'groq' requires LLM_API_KEY to be set.")
        return GroqLLMClient(
            api_key=settings.llm_api_key,
            model_name=settings.llm_model,
        )

    if provider in {"openai", "azure_openai", "anthropic", "local"}:
        if not settings.llm_api_key:
            raise LLMConfigurationError(
                f"LLM_PROVIDER '{settings.llm_provider}' requires LLM_API_KEY."
            )
        raise LLMConfigurationError(
            f"LLM provider '{settings.llm_provider}' is configured but not yet implemented."
        )

    raise LLMConfigurationError(
        f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. Supported options: 'mock', 'gemini', 'groq'."
    )

