import pytest

from src.evals import agent
from src.evals.agent import resolve_route
from src.tools.tool import Tool


def _clear_keys(monkeypatch: pytest.MonkeyPatch):
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(key, raising=False)


def test_falls_back_to_openrouter_when_direct_key_absent(monkeypatch: pytest.MonkeyPatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")

    for model_name in ("gpt-5.4", "claude-sonnet-4.6", "gemini-2.5-flash", "qwen-3.5-flash"):
        route = resolve_route(model_name)
        assert route.provider == "openrouter"
        assert route.base_url == agent._OPENROUTER_BASE_URL
        assert route.api_key == "or-key"
        assert "/" in route.model_id


def test_routes_direct_when_provider_key_present(monkeypatch: pytest.MonkeyPatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("OPENAI_API_KEY", "oa-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gm-key")

    openai_route = resolve_route("gpt-5.4")
    assert openai_route.provider == "openai"
    assert openai_route.base_url == "https://api.openai.com/v1"
    assert openai_route.model_id == "gpt-5.4"
    assert openai_route.api_key == "oa-key"

    anthropic_route = resolve_route("claude-sonnet-4.6")
    assert anthropic_route.provider == "anthropic"
    assert anthropic_route.base_url == "https://api.anthropic.com/v1"
    assert anthropic_route.model_id == "claude-sonnet-4-6"
    assert anthropic_route.api_key == "an-key"

    google_route = resolve_route("gemini-2.5-flash")
    assert google_route.provider == "google"
    assert google_route.model_id == "gemini-2.5-flash"
    assert google_route.api_key == "gm-key"

    openrouter_route = resolve_route("qwen-3.5-flash")
    assert openrouter_route.provider == "openrouter"
    assert openrouter_route.api_key == "or-key"


def test_missing_specific_direct_key_falls_back(monkeypatch: pytest.MonkeyPatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-key")

    openai_route = resolve_route("gpt-5.4")
    assert openai_route.provider == "openrouter"
    assert openai_route.model_id == "openai/gpt-5.4"

    anthropic_route = resolve_route("claude-sonnet-4.6")
    assert anthropic_route.provider == "anthropic"


def test_missing_openrouter_key_raises(monkeypatch: pytest.MonkeyPatch):
    _clear_keys(monkeypatch)
    with pytest.raises(OSError):
        resolve_route("qwen-3.5-flash")


def test_unknown_model_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    with pytest.raises(ValueError):
        resolve_route("not-a-model")


def test_shared_client_is_reused_across_calls_and_threads():
    import threading

    agent._shared_clients.clear()
    seen: list[object] = []

    def worker():
        seen.append(agent._get_openai_client("k", agent._OPENROUTER_BASE_URL))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len({id(c) for c in seen}) == 1
    assert len(agent._shared_clients) == 1


def test_distinct_endpoints_get_distinct_clients():
    agent._shared_clients.clear()
    a = agent._get_openai_client("k", "https://api.openai.com/v1")
    b = agent._get_openai_client("k", "https://api.anthropic.com/v1")
    assert a is not b
    assert len(agent._shared_clients) == 2


def test_invalidate_client_drops_and_rebuilds():
    agent._shared_clients.clear()
    first = agent._get_openai_client("k", agent._OPENROUTER_BASE_URL)
    agent._invalidate_client(first)
    assert len(agent._shared_clients) == 0
    second = agent._get_openai_client("k", agent._OPENROUTER_BASE_URL)
    assert second is not first


def test_sanitized_tool_schemas_round_trip():
    tools = [
        Tool(name="calendar.delete_event", func=lambda: "", description="d", args_schema={}, signature_str=""),
        Tool(
            name="calendar.get_event_information_by_id",
            func=lambda: "",
            description="d",
            args_schema={},
            signature_str="",
        ),
    ]
    schemas, original_by_sanitized = agent._sanitized_tool_schemas(tools)

    for schema in schemas:
        name = schema["function"]["name"]
        assert "." not in name
        assert original_by_sanitized[name].startswith("calendar.")

    assert original_by_sanitized["calendar_delete_event"] == "calendar.delete_event"
    assert original_by_sanitized["calendar_get_event_information_by_id"] == "calendar.get_event_information_by_id"
