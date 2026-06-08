import httpx
import openai

from src.evals.inference import _is_context_window_error

_REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


def test_bad_request_with_context_code_is_detected_by_type():
    exc = openai.BadRequestError(
        "Bad request",
        response=httpx.Response(400, request=_REQUEST),
        body={"code": "context_length_exceeded"},
    )
    assert _is_context_window_error(exc)


def test_message_pattern_is_detected():
    assert _is_context_window_error(RuntimeError("This model's prompt is too long"))


def test_bad_request_without_context_signal_is_not_detected():
    exc = openai.BadRequestError(
        "Invalid value for 'temperature'",
        response=httpx.Response(400, request=_REQUEST),
        body={"code": "invalid_request_error"},
    )
    assert not _is_context_window_error(exc)


def test_unrelated_error_is_not_detected():
    assert not _is_context_window_error(ValueError("some other failure"))
