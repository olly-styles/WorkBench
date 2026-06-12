"""Generate retro/data/model_results.json from the committed per-task results.

This is the single source of truth for the WorkBench Revisited (2026) figures:
every correct/side-effect count in retro/figs/ is read from the JSON this
script writes, and the JSON itself is derived from the results CSVs in
data/results/ via the same scoring pipeline as workbench-evaluate. Re-run it
after committing new results:

    uv run scripts/evals/generate_results_summary.py
"""

import json
import sys
import warnings
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from src.evals.metrics import (  # noqa: E402
    get_latest_results_from_dir,
    get_latest_results_path,
    ground_truth_version_for_results,
)

TOOLS = [
    "calendar",
    "email",
    "analytics",
    "project_management",
    "customer_relationship_manager",
    "multi_domain",
]

RETRO_MODELS = {
    "GPT-3.5-turbo": "gpt-3.5",
    "GPT-4-turbo": "gpt-4-turbo",
    "GPT-4o": "gpt-4o",
    "GPT-4.1": "gpt-4.1",
    "o3": "o3",
    "GPT-5": "gpt-5",
    "GLM-4.6": "glm-4.6",
    "Haiku 4.5": "claude-haiku-4.5",
    "GPT-5.1": "gpt-5.1",
    "GPT-5.2": "gpt-5.2",
    "Sonnet 4.6": "claude-sonnet-4.6",
    "Gemini-3.1-pro": "gemini-3.1-pro",
    "Qwen3.5": "qwen-3.5-flash",
    "GPT-5.4-nano": "gpt-5.4-nano",
    "GPT-5.4-mini": "gpt-5.4-mini",
    "GPT-5.4": "gpt-5.4",
    "Mistral-Small-4": "mistral-small-2603",
    "Kimi-K2.6": "kimi-k2.6",
    "GPT-5.5": "gpt-5.5",
    "DeepSeek-V4-pro": "deepseek-v4-pro",
    "Mistral-Medium-3.5": "mistral-medium-3-5",
    "Gemini-3.5-flash": "gemini-3.5-flash",
    "Opus 4.8": "claude-opus-4.8",
    "Fable 5": "claude-fable-5",
}

OUTPUT_PATH = _ROOT / "retro" / "data" / "model_results.json"


def summarize_model(model: str) -> dict:
    per_tool = {}
    sources = {}
    correct = side_effects = total = 0
    for tool in TOOLS:
        paths = get_latest_results_path("data/results", model, tool, all_tools_in_prompt=True)
        if paths is None:
            raise FileNotFoundError(f"No committed results for {model}/{tool} under data/results/{tool}/.")
        summary = get_latest_results_from_dir("data/results", model, tool, print_errors=False)
        assert summary is not None
        tool_total = summary.num_correct + summary.num_incorrect
        per_tool[tool] = {
            "correct": int(summary.num_correct),
            "side_effects": int(summary.num_side_effects),
            "total": int(tool_total),
        }
        sources[tool] = str(Path(paths[0]).as_posix())
        correct += summary.num_correct
        side_effects += summary.num_side_effects
        total += tool_total
    return {
        "model_name": model,
        "correct": int(correct),
        "side_effects": int(side_effects),
        "total": int(total),
        "ground_truth_version": ground_truth_version_for_results(sources["calendar"]),
        "per_tool": per_tool,
        "sources": sources,
    }


def main() -> None:
    warnings.filterwarnings("ignore")
    models = {}
    for label, model in RETRO_MODELS.items():
        print(f"Scoring {label} ({model})...")
        models[label] = summarize_model(model)
    payload = {
        "description": "Per-model WorkBench Revisited (2026) results, derived from the committed "
        "per-task results in data/results/ by scripts/evals/generate_results_summary.py. "
        "Do not edit by hand.",
        "total_tasks": 690,
        "models": models,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH.relative_to(_ROOT)} with {len(models)} models.")


if __name__ == "__main__":
    main()
