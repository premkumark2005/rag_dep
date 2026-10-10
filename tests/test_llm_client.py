"""Unit tests for GeminiLLMClient and GroqLLMClient."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.generation.llm_client import GeminiLLMClient, GroqLLMClient
from backend.utils.exceptions import (
    LLMGenerationError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
)

# ---------------------------------------------------------------------------
# Gemini tests – skipped automatically when google-genai is not installed
# ---------------------------------------------------------------------------

google_genai = pytest.importorskip("google.genai", reason="google-genai not installed")
APIError = pytest.importorskip("google.genai.errors", reason="google-genai not installed").APIError


def test_successful_gemini_request():
    mock_response = MagicMock()
    mock_response.text = "Hello World"

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="dummy_key")
        result = client.generate("Say hello")

        assert result == "Hello World"
        mock_client.models.generate_content.assert_called_once()


def test_temporary_503_followed_by_success():
    mock_success = MagicMock()
    mock_success.text = "Success on attempt 2"

    mock_error = APIError(code=503, response_json={"error": {"message": "Service Unavailable"}})

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.models.generate_content.side_effect = [mock_error, mock_success]

        client = GeminiLLMClient(api_key="dummy_key")
        with patch("time.sleep") as mock_sleep:
            result = client.generate("Try again")
            assert result == "Success on attempt 2"
            assert mock_client.models.generate_content.call_count == 2
            mock_sleep.assert_called_once_with(1.0)


def test_repeated_503_failure():
    mock_error = APIError(code=503, response_json={"error": {"message": "Service Unavailable"}})

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.models.generate_content.side_effect = [mock_error] * 5

        client = GeminiLLMClient(api_key="dummy_key")
        with patch("time.sleep") as mock_sleep:
            with pytest.raises(LLMServiceUnavailableError) as exc_info:
                client.generate("Fail me")
            assert "service unavailable" in str(exc_info.value).lower()
            assert mock_client.models.generate_content.call_count == 4  # 1 initial + 3 retries
            assert mock_sleep.call_count == 3


def test_timeout_retry_and_failure():
    mock_error = httpx.TimeoutException("Connection timed out")

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.models.generate_content.side_effect = [mock_error] * 5

        client = GeminiLLMClient(api_key="dummy_key")
        with patch("time.sleep") as mock_sleep:
            with pytest.raises(LLMGenerationError) as exc_info:
                client.generate("Time out")
            assert "failed after 4 attempts" in str(exc_info.value).lower()
            assert mock_client.models.generate_content.call_count == 4
            assert mock_sleep.call_count == 3


def test_rate_limit_error():
    mock_error = APIError(code=429, response_json={"error": {"message": "Resource Exhausted"}})

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.models.generate_content.side_effect = [mock_error] * 5

        client = GeminiLLMClient(api_key="dummy_key")
        with patch("time.sleep") as mock_sleep:
            with pytest.raises(LLMRateLimitError) as exc_info:
                client.generate("Limit me")
            assert "rate limit exceeded" in str(exc_info.value).lower()
            assert mock_client.models.generate_content.call_count == 4
            assert mock_sleep.call_count == 3


# ---------------------------------------------------------------------------
# Groq tests – always available (groq package is installed)
# ---------------------------------------------------------------------------

class _FakeGroqCompletion:
    """Minimal stub mimicking groq.types.chat.ChatCompletion."""

    def __init__(self, content: str):
        msg = MagicMock()
        msg.content = content
        choice = MagicMock()
        choice.message = msg
        self.choices = [choice]


class _FakeGroqError(Exception):
    """Stub for groq API errors with a status_code attribute."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def _make_groq_client(api_key: str = "dummy_groq_key"):
    """Create a GroqLLMClient with the underlying groq.Groq mocked out."""
    with patch("groq.Groq"):
        client = GroqLLMClient(api_key=api_key)
    return client


def test_groq_successful_request():
    client = _make_groq_client()
    client.client.chat.completions.create.return_value = _FakeGroqCompletion("Groq answer")

    result = client.generate("Say something")
    assert result == "Groq answer"
    client.client.chat.completions.create.assert_called_once()


def test_groq_temporary_503_then_success():
    client = _make_groq_client()
    err = _FakeGroqError("Service Unavailable", 503)
    client.client.chat.completions.create.side_effect = [
        err,
        _FakeGroqCompletion("Recovered"),
    ]

    with patch("time.sleep") as mock_sleep:
        result = client.generate("Retry me")
    assert result == "Recovered"
    assert client.client.chat.completions.create.call_count == 2
    mock_sleep.assert_called_once_with(1.0)


def test_groq_exhausted_503_retries():
    client = _make_groq_client()
    err = _FakeGroqError("Service Unavailable", 503)
    client.client.chat.completions.create.side_effect = [err] * 5

    with patch("time.sleep"):
        with pytest.raises(LLMServiceUnavailableError):
            client.generate("Always fail")

    assert client.client.chat.completions.create.call_count == 4  # 1 + 3 retries


def test_groq_rate_limit_error():
    client = _make_groq_client()
    err = _FakeGroqError("rate limit exceeded", 429)
    client.client.chat.completions.create.side_effect = [err] * 5

    with patch("time.sleep"):
        with pytest.raises(LLMRateLimitError):
            client.generate("Rate limited")


def test_groq_empty_response_raises():
    client = _make_groq_client()
    client.client.chat.completions.create.return_value = _FakeGroqCompletion("")

    with pytest.raises(LLMGenerationError, match="empty text response"):
        client.generate("Return nothing")
