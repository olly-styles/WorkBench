"""Loader for the generated results artifact behind the Revisited figures.

The artifact is written by scripts/evals/generate_results_summary.py from the
committed per-task results; figure scripts read counts from here instead of
hard-coding them.
"""

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "model_results.json"


def load_model_results() -> dict[str, dict]:
    with open(DATA_PATH) as f:
        return json.load(f)["models"]
