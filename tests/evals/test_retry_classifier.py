import httpx
import openai

from src.evals.agent import _HARD_DEADLINE_SECONDS, _is_retryable

_REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


def _status_error(cls: type[openai.APIStatusError], status_code: int):
    return cls("boom", response=httpx.Response(status_code, request=_REQUEST), body=None)


def test_hard_deadline_timeout_is_retryable():
    exc = TimeoutError(f"LLM call exceeded {_HARD_DEADLINE_SECONDS}s wall-clock deadline; client closed")
    assert _is_retryable(exc)


def test_rate_limit_is_retryable():
    assert _is_retryable(_status_error(openai.RateLimitError, 429))


def test_internal_server_error_is_retryable():
    assert _is_retryable(_status_error(openai.InternalServerError, 500))


def test_api_connection_error_is_retryable():
    assert _is_retryable(openai.APIConnectionError(request=_REQUEST))


def test_api_timeout_error_is_retryable():
    assert _is_retryable(openai.APITimeoutError(request=_REQUEST))


def test_bad_request_is_not_retryable():
    assert not _is_retryable(_status_error(openai.BadRequestError, 400))


def test_authentication_error_is_not_retryable():
    assert not _is_retryable(_status_error(openai.AuthenticationError, 401))


def test_value_error_is_not_retryable():
    assert not _is_retryable(ValueError("Unknown model: foo"))


def test_assertion_error_is_not_retryable():
    assert not _is_retryable(AssertionError("invariant violated"))
