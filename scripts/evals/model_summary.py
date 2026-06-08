import glob
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env")

from scripts.evals.estimate_model_costs import (  # noqa: E402
    CHARS_PER_TOKEN,
    DOMAINS,
    PRICING,
    _structured_call_overhead_chars,
)
from src.evals.metrics import get_latest_results_from_dir  # noqa: E402

TOTAL_TASKS = 690


def _metrics(model: str) -> tuple[int, int, int]:
    correct = incorrect = side_effects = 0
    for domain in DOMAINS:
        summary = None
        for _ in range(8):
            try:
                summary = get_latest_results_from_dir("data/results", model, domain, False, True)
                break
            except AssertionError:
                time.sleep(1)
        if summary is None:
            raise RuntimeError(f"metrics failed for {model}/{domain}")
        correct += summary.num_correct
        incorrect += summary.num_incorrect
        side_effects += summary.num_side_effects
    return correct, incorrect, side_effects


def _cost(model: str, overhead_chars: int) -> float:
    p_in, p_out = PRICING[model]
    calls = hist = out = 0
    for domain in DOMAINS:
        fs = sorted(glob.glob(str(_ROOT / f"data/results/{domain}/{model}_all_*_traces.json")))
        if not fs:
            raise RuntimeError(f"no traces for {model}/{domain}")
        with open(fs[-1]) as f:
            entries = json.load(f)
        for entry in entries:
            for step in entry.get("steps", []):
                calls += 1
                hist += len(str(step.get("llm_input") or ""))
                out += len(str(step.get("llm_output") or ""))
    input_tok = (calls * overhead_chars + hist) / CHARS_PER_TOKEN
    output_tok = out / CHARS_PER_TOKEN
    return input_tok / 1e6 * p_in + output_tok / 1e6 * p_out


def main() -> None:
    overhead = _structured_call_overhead_chars()
    for model in sys.argv[1:]:
        correct, incorrect, side_effects = _metrics(model)
        total = correct + incorrect
        cost = _cost(model, overhead)
        print(
            f"{model}: correct={correct}/{total} ({correct / total * 100:.1f}%) "
            f"side_effects={side_effects} ({side_effects / total * 100:.1f}%) "
            f"total_cost=${cost:.2f} cost_per_task=${cost / TOTAL_TASKS:.4f}"
        )


if __name__ == "__main__":
    main()
