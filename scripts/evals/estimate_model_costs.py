"""Estimate the no-caching API cost of a full benchmark run, per model.

Token usage is not recorded in the traces, so input and output tokens are
approximated from the logged ``llm_input`` / ``llm_output`` strings at
``CHARS_PER_TOKEN`` characters per token. ``llm_input`` is only the running
message history; in a structured-output run every call also re-sends the
system prompt and the full tool schema, which dominate input volume, so that
fixed per-call overhead is added back here.

Prices are hard-coded dollars per million tokens as ``(input, output)`` for
the standard, no-caching tier, fetched 2026-06-03 (see ``PRICING`` for the
source of each rate). Caching would materially lower the real bill for
providers that cache implicitly; this script deliberately reports the
uncached figure.

Each model's cost is computed from its own traces. Models priced in ``PRICING``
that have no traces on disk are skipped.

Usage:
    uv run python scripts/evals/estimate_model_costs.py
"""

import csv
import glob
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
csv.field_size_limit(sys.maxsize)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env")

from src.evals.agent import ACT_WITHOUT_CONFIRMATION_SUFFIX, _sanitized_tool_schemas  # noqa: E402
from src.evals.inference import HARDCODED_CURRENT_TIME, get_toolkits  # noqa: E402
from src.evals.metrics import ALL_DOMAINS as DOMAINS  # noqa: E402

CHARS_PER_TOKEN = 4.0

# Dollars per million tokens, (input, output), standard no-caching tier.
# Fetched 2026-06-03 from each provider / OpenRouter model page.
PRICING: dict[str, tuple[float, float]] = {
    "claude-fable-5": (10.00, 50.00),
    "claude-opus-4.8": (5.00, 25.00),
    "claude-opus-4.7": (5.00, 25.00),
    "claude-opus-4.6": (5.00, 25.00),
    "claude-opus-4.5": (5.00, 25.00),  # 67% cut at 4.5, held since
    "claude-opus-4.1": (15.00, 75.00),
    "claude-opus-4": (15.00, 75.00),
    "claude-sonnet-4.6": (3.00, 15.00),
    "claude-sonnet-4.5": (3.00, 15.00),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-haiku-4.5": (1.00, 5.00),
    "gpt-5.5": (5.00, 30.00),
    "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5.4-nano": (0.20, 1.25),
    "gpt-4-turbo": (10.00, 30.00),
    "gemini-3.5-flash": (1.50, 9.00),
    "gemini-3.1-pro": (2.00, 12.00),
    # deepseek-v4-pro: launch-promo rate; regular is 1.74 / 3.48.
    "deepseek-v4-pro": (0.435, 0.87),
    "qwen-3.5-flash": (0.065, 0.26),
    # Fetched 2026-06-12 from the OpenRouter models API.
    "kimi-k2.6": (0.67, 3.39),
    "glm-4.6": (0.43, 1.74),
    "mistral-small-2603": (0.15, 0.60),
    "mistral-medium-3-5": (1.50, 7.50),
    "gemini-3-flash": (0.50, 3.00),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gpt-5-nano": (0.05, 0.40),
    "gpt-4": (30.00, 60.00),
    # Original-paper models with no 2026 traces (always skipped) and, for the
    # OpenRouter-served pair, delisted from OpenRouter; rates are the last
    # public list prices and are approximate.
    "claude-2": (8.00, 24.00),
    "llama2-70b": (0.70, 0.90),
    "mixtral-8x7b": (0.24, 0.24),
    # Prior-generation and gpt-5-line OpenAI models; public list prices fetched
    # 2026-06-04. o1 is priced for reference but was not run this round.
    "gpt-3.5": (0.50, 1.00),  # gpt-3.5-turbo; classic 0125 output was 1.50
    "gpt-4o": (2.50, 10.00),
    "o1": (15.00, 60.00),
    "o3": (2.00, 8.00),  # current rate; launch was 10.00 / 40.00
    "gpt-4.1": (2.00, 8.00),
    "gpt-5": (1.25, 10.00),
    "gpt-5.1": (1.25, 10.00),
    "gpt-5.2": (1.75, 14.00),
    "gpt-5.4": (2.50, 15.00),
}


def _structured_call_overhead_chars() -> int:
    """Chars re-sent on every structured-output call: system prompt + tool schema."""
    tools = get_toolkits(["email", "calendar", "analytics", "project_management", "customer_relationship_manager"])
    schema, _ = _sanitized_tool_schemas(tools)
    datetime_prefix = (
        f"Today's date is {HARDCODED_CURRENT_TIME.strftime('%A')}, {HARDCODED_CURRENT_TIME.date()} "
        f"and the current time is {HARDCODED_CURRENT_TIME.time()}. "
        f"Remember the current date and time when completing tasks. "
        f"Meetings must not start before 9am or end after 6pm."
    )
    system_prompt = datetime_prefix + " " + ACT_WITHOUT_CONFIRMATION_SUFFIX.strip()
    return len(system_prompt) + len(json.dumps(schema))


def _latest_trace(model: str, domain: str) -> str | None:
    fs = sorted(glob.glob(str(_ROOT / f"data/results/{domain}/{model}_all_*_traces.json")))
    return fs[-1] if fs else None


def _usage(model: str, overhead_chars: int) -> dict | None:
    calls = tasks = hist_chars = out_chars = 0
    for domain in DOMAINS:
        path = _latest_trace(model, domain)
        if path is None:
            return None
        with open(path) as f:
            entries = json.load(f)
        for entry in entries:
            tasks += 1
            for step in entry.get("steps", []):
                calls += 1
                hist_chars += len(str(step.get("llm_input") or ""))
                out_chars += len(str(step.get("llm_output") or ""))
    input_tok = (calls * overhead_chars + hist_chars) / CHARS_PER_TOKEN
    output_tok = out_chars / CHARS_PER_TOKEN
    return {"tasks": tasks, "calls": calls, "input_tok": input_tok, "output_tok": output_tok}


def main() -> None:
    overhead_chars = _structured_call_overhead_chars()
    print(f"per-call structured overhead ~ {overhead_chars / CHARS_PER_TOKEN:,.0f} tok (system prompt + tool schema)\n")

    rows = []
    for model, (p_in, p_out) in PRICING.items():
        usage = _usage(model, overhead_chars)
        if usage is None:
            continue
        cost = usage["input_tok"] / 1e6 * p_in + usage["output_tok"] / 1e6 * p_out
        rows.append((model, usage, cost))

    rows.sort(key=lambda r: -r[2])
    header = f"{'model':<20}{'calls':>7}{'input':>10}{'output':>9}{'$/Mtok in/out':>16}{'cost':>9}{'cost/task':>11}"
    print(header)
    print("-" * len(header))
    for model, u, cost in rows:
        p_in, p_out = PRICING[model]
        print(
            f"{model:<20}{u['calls']:>7}{u['input_tok'] / 1e6:>9.1f}M{u['output_tok'] / 1e3:>8.0f}k"
            f"{f'{p_in}/{p_out}':>16}{f'${cost:.2f}':>9}{f'${cost / u["tasks"]:.4f}':>11}"
        )


if __name__ == "__main__":
    main()
