import contextlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, NamedTuple

import openai
from openai.types.chat import ChatCompletion
from tenacity import RetryCallState, retry, retry_if_exception, stop_after_attempt, wait_random_exponential

from src.tools.tool import Tool, render_tool_description, tool_to_openai_schema

PREFIX = "Respond to the human as helpfully and accurately as possible. You have access to the following tools:"

FORMAT_INSTRUCTIONS = """Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Provide only ONE action per $JSON_BLOB, as shown:

```
{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}
```

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond
Action:
```
{
  "action": "Final Answer",
  "action_input": "Final response to human"
}
```"""

SUFFIX = "Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation:."

ACT_WITHOUT_CONFIRMATION_SUFFIX = (
    " Do not ask for confirmation before executing actions."
    " Execute actions immediately and continue until the task is fully complete."
    " Do not stop after a search or lookup step."
)

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Per-provider direct endpoints. OpenAI and Anthropic credits only bill when
# called directly (not via OpenRouter); Anthropic and Google are reached
# through their OpenAI-compatible chat-completions endpoints so the same
# unified agent loop works for every provider.
_PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
    "openrouter": _OPENROUTER_BASE_URL,
}

_PROVIDER_API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

# Per-syscall httpx timeout — note this is the max idle gap between bytes,
# NOT a total wall-clock deadline. Cloudflare-fronted endpoints can dribble
# keepalive bytes during a slow upstream which resets this timer
# indefinitely; the hard deadline below is what actually unblocks us.
_REQUEST_TIMEOUT_SECONDS = 60.0

# Total wall-clock deadline for one chat.completions.create. If it expires
# we close the in-flight client to abort the SSL read and let tenacity
# retry with a fresh client.
_HARD_DEADLINE_SECONDS = 75.0

# Connection pool size for each shared client. Each worker issues one request
# at a time, so this caps useful concurrency; sized well above any sane worker
# count so the pool never blocks request acquisition.
_POOL_SIZE = 256

_client_lock = threading.Lock()
_shared_clients: dict[tuple[str, str], openai.OpenAI] = {}


def _get_openai_client(api_key: str, base_url: str) -> openai.OpenAI:
    """Return a process-wide shared OpenAI client for ``(api_key, base_url)``.

    The openai/httpx client is thread-safe and pools connections, so one
    shared client per endpoint serves every worker. Connections are kept
    alive and reused, avoiding a TCP+TLS handshake per request (measured
    ~30% faster at 64-way concurrency than a fresh-handshake-per-request
    client). If a request trips the hard wall-clock deadline, the watchdog
    closes the client to abort the wedged read and ``_invalidate_client``
    drops it from the cache so the next call rebuilds it; concurrent requests
    on the closed client error and are retried by tenacity.
    """
    import httpx
    from openai import OpenAI

    cache_key = (api_key, base_url)
    with _client_lock:
        client = _shared_clients.get(cache_key)
        if client is None:
            http_client = httpx.Client(
                timeout=httpx.Timeout(connect=10.0, read=_REQUEST_TIMEOUT_SECONDS, write=10.0, pool=10.0),
                limits=httpx.Limits(max_keepalive_connections=_POOL_SIZE, max_connections=_POOL_SIZE),
            )
            client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client, max_retries=0)
            _shared_clients[cache_key] = client
        return client


def _invalidate_client(stale: openai.OpenAI) -> None:
    with _client_lock:
        for key, client in list(_shared_clients.items()):
            if client is stale:
                del _shared_clients[key]
                break
    with contextlib.suppress(Exception):
        stale.close()


def _create_with_deadline(client: openai.OpenAI, **kwargs: Any) -> ChatCompletion:
    """Run ``client.chat.completions.create`` with a hard wall-clock deadline.

    httpx's ``read`` timeout is the max idle gap between bytes, so a server
    that dribbles keepalive bytes can hang the call indefinitely (observed
    mid-eval: 3+ minutes stuck in ``_ssl__SSLSocket_read`` despite the
    per-syscall timeout). When the deadline trips we close the underlying
    HTTP client from a watchdog thread, which causes the in-flight SSL read
    to fail fast; tenacity then retries on a fresh client.
    """
    done = threading.Event()
    fired = threading.Event()

    def watchdog() -> None:
        if done.wait(_HARD_DEADLINE_SECONDS):
            return
        fired.set()
        with contextlib.suppress(Exception):
            client.close()

    t = threading.Thread(target=watchdog, daemon=True)
    t.start()
    try:
        return client.chat.completions.create(**kwargs)
    except Exception:
        if fired.is_set():
            _invalidate_client(client)
            raise TimeoutError(f"LLM call exceeded {_HARD_DEADLINE_SECONDS}s wall-clock deadline; client closed")
        raise
    finally:
        done.set()


def build_system_prompt(tools: list[Tool], datetime_prefix: str, act_without_confirmation: bool = False) -> str:
    tool_descriptions = "\n".join(render_tool_description(t) for t in tools)
    tool_names = ", ".join(f'"{t.name}"' for t in tools)
    format_block = FORMAT_INSTRUCTIONS.replace("{tool_names}", tool_names)
    suffix = SUFFIX + ACT_WITHOUT_CONFIRMATION_SUFFIX if act_without_confirmation else SUFFIX
    return datetime_prefix + "\n\n".join([PREFIX, tool_descriptions, format_block, suffix])


PARSE_ERROR = "__parse_error__"
FINAL_ANSWER = "Final Answer"
AGENT_STOPPED_MESSAGE = "Agent stopped due to iteration limit or time limit."


def parse_action(text: str) -> tuple[str, dict[str, str] | str]:
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if not match:
        json_match = re.search(r'\{\s*"action"\s*:', text, re.DOTALL)
        if json_match:
            start = json_match.start()
            brace_count = 0
            end = start
            for i in range(start, len(text)):
                if text[i] == "{":
                    brace_count += 1
                elif text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            raw = text[start:end]
        else:
            return FINAL_ANSWER, text.strip()
    else:
        raw = match.group(1).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return PARSE_ERROR, (
            f"Could not parse your action as JSON ({e}). "
            'Respond with a single JSON object with "action" and "action_input" keys.'
        )
    if not isinstance(parsed, dict):
        return PARSE_ERROR, 'Your action must be a JSON object with "action" and "action_input" keys.'
    action = parsed.get("action", FINAL_ANSWER)
    action_input = parsed.get("action_input", "")
    return action, action_input


# ---------------------------------------------------------------------------
# All LLM calls use the OpenAI-compatible chat-completions API. The endpoint
# (direct provider vs OpenRouter) is chosen per model by ``resolve_route``.
# ---------------------------------------------------------------------------


def _call_llm(route: "Route", system_prompt: str, human_msg: str, temperature: float) -> str:
    client = _get_openai_client(route.api_key, route.base_url)
    kwargs: dict = {
        "model": route.model_id,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": human_msg}],
    }
    if route.supports_temperature:
        kwargs["temperature"] = temperature
    response = _create_with_deadline(client, **kwargs)
    return response.choices[0].message.content or ""


def _call_llm_structured(
    route: "Route",
    system_prompt: str,
    messages: list[dict],
    tools_schema: list[dict],
    temperature: float,
) -> dict:
    client = _get_openai_client(route.api_key, route.base_url)
    kwargs: dict = {
        "model": route.model_id,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "tools": tools_schema,
    }
    if route.supports_temperature:
        kwargs["temperature"] = temperature
    response = _create_with_deadline(client, **kwargs)
    msg = response.choices[0].message
    tool_calls = []
    if msg.tool_calls:
        for tc in msg.tool_calls:
            assert tc.type == "function"
            tool_calls.append({"id": tc.id, "name": tc.function.name, "arguments": json.loads(tc.function.arguments)})
    return {"content": msg.content or "", "tool_calls": tool_calls}


class ModelConfig(NamedTuple):
    model_id: str
    supports_temperature: bool
    provider: str = "openrouter"


class Route(NamedTuple):
    model_id: str
    base_url: str
    api_key: str
    provider: str
    supports_temperature: bool


MODEL_REGISTRY: dict[str, ModelConfig] = {
    # Current-generation models
    "gpt-5.5": ModelConfig("openai/gpt-5.5", False, "openai"),
    "gpt-5.4": ModelConfig("openai/gpt-5.4", True, "openai"),
    "gpt-5.4-mini": ModelConfig("openai/gpt-5.4-mini", False, "openai"),
    "gpt-5.4-nano": ModelConfig("openai/gpt-5.4-nano", False, "openai"),
    "gpt-5.3": ModelConfig("openai/gpt-5.3", False, "openai"),
    "gpt-5.2": ModelConfig("openai/gpt-5.2", False, "openai"),
    "gpt-5.1": ModelConfig("openai/gpt-5.1", False, "openai"),
    "gpt-5": ModelConfig("openai/gpt-5", False, "openai"),
    "gpt-5-nano": ModelConfig("openai/gpt-5-nano", False, "openai"),
    "claude-opus-4.8": ModelConfig("anthropic/claude-opus-4-8", False, "anthropic"),
    "claude-opus-4.7": ModelConfig("anthropic/claude-opus-4-7", False, "anthropic"),
    "claude-opus-4.6": ModelConfig("anthropic/claude-opus-4-6", False, "anthropic"),
    "claude-opus-4.5": ModelConfig("anthropic/claude-opus-4-5-20251101", False, "anthropic"),
    "claude-opus-4.1": ModelConfig("anthropic/claude-opus-4-1-20250805", False, "anthropic"),
    "claude-opus-4": ModelConfig("anthropic/claude-opus-4-20250514", False, "anthropic"),
    "claude-sonnet-4.6": ModelConfig("anthropic/claude-sonnet-4-6", True, "anthropic"),
    "claude-sonnet-4.5": ModelConfig("anthropic/claude-sonnet-4-5-20250929", True, "anthropic"),
    "claude-sonnet-4": ModelConfig("anthropic/claude-sonnet-4-20250514", True, "anthropic"),
    "claude-haiku-4.5": ModelConfig("anthropic/claude-haiku-4-5", True, "anthropic"),
    "gemini-3.5-flash": ModelConfig("google/gemini-3.5-flash", True, "google"),
    "gemini-3.1-pro": ModelConfig("google/gemini-3.1-pro-preview", True, "google"),
    "gemini-3-flash": ModelConfig("google/gemini-3-flash-preview", True, "google"),
    "gemini-2.5-flash": ModelConfig("google/gemini-2.5-flash", True, "google"),
    "gemini-3.1-flash-lite": ModelConfig("google/gemini-3.1-flash-lite-preview", True, "google"),
    "qwen-3.5-flash": ModelConfig("qwen/qwen3.5-flash-02-23", True, "openrouter"),
    "deepseek-v4-pro": ModelConfig("deepseek/deepseek-v4-pro", True, "openrouter"),
    "kimi-k2.6": ModelConfig("moonshotai/kimi-k2.6", True, "openrouter"),
    "glm-4.6": ModelConfig("z-ai/glm-4.6", True, "openrouter"),
    # Prior-generation OpenAI models
    "gpt-4.1": ModelConfig("openai/gpt-4.1", True, "openai"),
    "o3": ModelConfig("openai/o3", False, "openai"),
    "o1": ModelConfig("openai/o1", False, "openai"),
    "gpt-4o": ModelConfig("openai/gpt-4o", True, "openai"),
    # Original paper models
    "gpt-4-turbo": ModelConfig("openai/gpt-4-turbo", True, "openai"),
    "gpt-4": ModelConfig("openai/gpt-4", True, "openai"),
    "gpt-3.5": ModelConfig("openai/gpt-3.5-turbo", True, "openai"),
    "claude-2": ModelConfig("anthropic/claude-2", True, "anthropic"),
    "llama2-70b": ModelConfig("meta-llama/llama-2-70b-chat", True, "openrouter"),
    "mixtral-8x7b": ModelConfig("mistralai/mixtral-8x7b-instruct", True, "openrouter"),
}


def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise OSError(f"Missing required environment variable '{key}'. Set it in your .env file.")
    return value


def resolve_route(model_name: str) -> Route:
    """Choose the endpoint, key, and model id for ``model_name``.

    A model's native provider (OpenAI, Anthropic, Google) is used directly
    when that provider's API key is present, so calls bill the credits we
    hold with that vendor. The OpenRouter slug carries a ``provider/`` prefix
    that the direct endpoints don't expect, so it is stripped. When the direct
    key is absent we fall back to OpenRouter with the original slug.
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_name}. Must be one of {list(MODEL_REGISTRY.keys())}")
    config = MODEL_REGISTRY[model_name]
    if config.provider != "openrouter":
        direct_key = os.environ.get(_PROVIDER_API_KEY_ENV[config.provider])
        if direct_key:
            direct_model_id = config.model_id.split("/", 1)[-1]
            return Route(
                direct_model_id,
                _PROVIDER_BASE_URLS[config.provider],
                direct_key,
                config.provider,
                config.supports_temperature,
            )
    openrouter_key = _require_env(_PROVIDER_API_KEY_ENV["openrouter"])
    return Route(config.model_id, _OPENROUTER_BASE_URL, openrouter_key, "openrouter", config.supports_temperature)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError | openai.APITimeoutError | openai.APIConnectionError | openai.RateLimitError):
        return True
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code >= 500
    return False


def _log_retry(retry_state: RetryCallState) -> None:
    assert retry_state.next_action is not None
    assert retry_state.outcome is not None
    print(
        f"Retryable error (attempt {retry_state.attempt_number}), "
        f"retrying in {retry_state.next_action.sleep:.1f}s: {retry_state.outcome.exception()!r}"
    )


@retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_random_exponential(multiplier=2, max=90),
    stop=stop_after_attempt(10),
    before_sleep=_log_retry,
    reraise=True,
)
def _call_llm_with_retry(route: Route, system_prompt: str, human_msg: str, temperature: float) -> str:
    return _call_llm(route, system_prompt, human_msg, temperature)


@retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_random_exponential(multiplier=2, max=90),
    stop=stop_after_attempt(10),
    before_sleep=_log_retry,
    reraise=True,
)
def _call_llm_structured_with_retry(
    route: Route,
    system_prompt: str,
    messages: list[dict],
    tools_schema: list[dict],
    temperature: float,
) -> dict:
    return _call_llm_structured(route, system_prompt, messages, tools_schema, temperature)


def call_llm(model_name: str, system_prompt: str, human_msg: str, temperature: float) -> str:
    route = resolve_route(model_name)
    return _call_llm_with_retry(route, system_prompt, human_msg, temperature)


@dataclass
class TraceStep:
    llm_input: str
    llm_output: str
    action: str
    action_input: dict[str, str] | str
    observation: str


@dataclass
class AgentResult:
    output: str
    intermediate_steps: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    trace: list[TraceStep] = field(default_factory=list)


def run_agent(
    model_name: str,
    tools: list[Tool],
    task: str,
    datetime_prefix: str,
    max_iterations: int = 20,
    max_execution_time: float = 600,
    temperature: float = 0,
    act_without_confirmation: bool = False,
) -> AgentResult:
    system_prompt = build_system_prompt(tools, datetime_prefix, act_without_confirmation)
    tool_map = {t.name: t for t in tools}
    scratchpad = ""
    steps: list[tuple[str, dict[str, str]]] = []
    trace: list[TraceStep] = []
    start_time = time.time()

    for _ in range(max_iterations):
        if time.time() - start_time > max_execution_time:
            return AgentResult(
                output=AGENT_STOPPED_MESSAGE,
                intermediate_steps=steps,
                trace=trace,
            )

        human_msg = task + "\n\nThought:" + scratchpad
        response_text = call_llm(model_name, system_prompt, human_msg, temperature)
        action, action_input = parse_action(response_text)

        if action == FINAL_ANSWER:
            output = action_input if isinstance(action_input, str) else json.dumps(action_input)
            trace.append(
                TraceStep(
                    llm_input=human_msg,
                    llm_output=response_text,
                    action=action,
                    action_input=action_input,
                    observation="",
                )
            )
            return AgentResult(output=output, intermediate_steps=steps, trace=trace)

        if action == PARSE_ERROR:
            observation = action_input if isinstance(action_input, str) else str(action_input)
            trace.append(
                TraceStep(
                    llm_input=human_msg,
                    llm_output=response_text,
                    action=action,
                    action_input=action_input,
                    observation=observation,
                )
            )
            scratchpad += response_text + f"\nObservation: {observation}\nThought:"
            continue

        if action not in tool_map:
            observation = f"Tool '{action}' not found. Available tools: {', '.join(tool_map.keys())}"
        else:
            t = tool_map[action]
            if isinstance(action_input, dict):
                str_input = {k: str(v) for k, v in action_input.items()}
                observation = str(t.func(**str_input))
            else:
                observation = str(t.func(str(action_input)))

        trace.append(
            TraceStep(
                llm_input=human_msg,
                llm_output=response_text,
                action=action,
                action_input=action_input,
                observation=observation,
            )
        )
        steps.append((action, action_input if isinstance(action_input, dict) else {"input": str(action_input)}))
        scratchpad += response_text + f"\nObservation: {observation}\nThought:"

    return AgentResult(
        output=AGENT_STOPPED_MESSAGE,
        intermediate_steps=steps,
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Structured-outputs mode: native API tool calling
# ---------------------------------------------------------------------------


# Native tool-calling APIs (OpenAI, Anthropic) require function names to match
# ^[a-zA-Z0-9_-]+$, which rejects the dotted toolkit names (e.g.
# "calendar.delete_event"). OpenRouter tolerated the dots; the direct endpoints
# do not. We send sanitized names to the model and map them back to the
# original dotted names for execution and scoring.
def _sanitize_tool_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


def _sanitized_tool_schemas(tools: list[Tool]) -> tuple[list[dict], dict[str, str]]:
    schemas: list[dict] = []
    original_by_sanitized: dict[str, str] = {}
    for t in tools:
        sanitized = _sanitize_tool_name(t.name)
        existing = original_by_sanitized.get(sanitized)
        if existing is not None and existing != t.name:
            raise ValueError(
                f"Tool name collision after sanitization: '{t.name}' and '{existing}' both map to '{sanitized}'"
            )
        original_by_sanitized[sanitized] = t.name
        schema = tool_to_openai_schema(t)
        schema["function"]["name"] = sanitized
        schemas.append(schema)
    return schemas, original_by_sanitized


def run_agent_structured(
    model_name: str,
    tools: list[Tool],
    task: str,
    datetime_prefix: str,
    max_iterations: int = 20,
    max_execution_time: float = 600,
    temperature: float = 0,
    act_without_confirmation: bool = False,
) -> AgentResult:
    """Run the agent using native API tool calling instead of ReAct text parsing."""
    route = resolve_route(model_name)

    tools_schema, original_by_sanitized = _sanitized_tool_schemas(tools)
    tool_map = {t.name: t for t in tools}

    system_prompt = datetime_prefix
    if act_without_confirmation:
        system_prompt += " " + ACT_WITHOUT_CONFIRMATION_SUFFIX.strip()

    messages: list[dict] = [{"role": "user", "content": task}]
    steps: list[tuple[str, dict[str, str]]] = []
    trace: list[TraceStep] = []
    start_time = time.time()

    for _ in range(max_iterations):
        if time.time() - start_time > max_execution_time:
            return AgentResult(
                output=AGENT_STOPPED_MESSAGE,
                intermediate_steps=steps,
                trace=trace,
            )

        response = _call_llm_structured_with_retry(route, system_prompt, messages, tools_schema, temperature)

        for tc in response["tool_calls"]:
            tc["name"] = _sanitize_tool_name(tc["name"])

        if not response["tool_calls"]:
            trace.append(
                TraceStep(
                    llm_input=str(messages),
                    llm_output=response["content"],
                    action=FINAL_ANSWER,
                    action_input=response["content"],
                    observation="",
                )
            )
            return AgentResult(output=response["content"], intermediate_steps=steps, trace=trace)

        # Build assistant message with tool calls for conversation history
        assistant_msg: dict = {
            "role": "assistant",
            "content": response["content"],
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])},
                }
                for tc in response["tool_calls"]
            ],
        }
        messages.append(assistant_msg)

        tool_result_messages: list[dict] = []
        for tool_call in response["tool_calls"]:
            action = str(original_by_sanitized.get(tool_call["name"], tool_call["name"]))
            action_input = tool_call["arguments"]

            if action not in tool_map:
                observation = f"Tool '{action}' not found. Available tools: {', '.join(tool_map.keys())}"
            else:
                t = tool_map[action]
                str_input = {k: str(v) for k, v in action_input.items()} if isinstance(action_input, dict) else {}
                observation = str(t.func(**str_input))

            trace.append(
                TraceStep(
                    llm_input=str(messages),
                    llm_output=json.dumps({"tool_call": tool_call, "content": response["content"]}),
                    action=action,
                    action_input=action_input if isinstance(action_input, dict) else {"input": str(action_input)},
                    observation=observation,
                )
            )
            steps.append((action, action_input if isinstance(action_input, dict) else {"input": str(action_input)}))
            tool_result_messages.append({"role": "tool", "tool_call_id": tool_call["id"], "content": observation})

        messages.extend(tool_result_messages)

    return AgentResult(
        output=AGENT_STOPPED_MESSAGE,
        intermediate_steps=steps,
        trace=trace,
    )
