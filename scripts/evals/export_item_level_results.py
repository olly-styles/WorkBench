"""Export item-level (per model, per task) results to data/results/item_level_results.csv.gz.

The aggregate numbers in the paper and in retro/data/model_results.json are
sums over per-task correct / side-effect verdicts that workbench-evaluate
computes on the fly and never writes out. This script scores every committed
results file in data/results/<domain>/ with the same pipeline and writes one
row per (run, task) so the disaggregated verdicts can be analysed without
re-running the evaluator. Re-run it after committing new results:

    uv run scripts/evals/export_item_level_results.py

Each run is scored against the ground-truth version recorded in its _meta.json
sidecar (v1 for the March 2024 paper runs). Rows are tagged with a run_group:

- revisited_2026: the runs behind retro/data/model_results.json (WorkBench Revisited)
- original_2024:  the March 2024 runs from the original paper
- other:          committed runs outside both published sets

The revisited_2026 rows are asserted to reproduce model_results.json exactly.
"""

import json
import re
import sys
import warnings
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from scripts.evals.generate_results_summary import OUTPUT_PATH as MODEL_RESULTS_PATH  # noqa: E402
from scripts.evals.generate_results_summary import RETRO_MODELS, TOOLS  # noqa: E402
from src.evals.metrics import (  # noqa: E402
    RESULTS_SUFFIXES,
    ground_truth_path,
    ground_truth_version_for_results,
    load_and_score_results,
    meta_path_for_results,
    strip_results_suffix,
)

RESULTS_ROOT = _ROOT / "data" / "results"
OUTPUT_PATH = RESULTS_ROOT / "item_level_results.csv.gz"

RESULTS_FILENAME = re.compile(
    r"^(?P<model>.+?)_(?P<tool_selection>all|domains)_(?P<run_timestamp>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})$"
)

COLUMNS = [
    "run_group",
    "model",
    "tool_selection",
    "run_timestamp",
    "ground_truth_version",
    "results_file",
    "domain",
    "task_id",
    "task",
    "base_template",
    "chosen_template",
    "task_domains",
    "ground_truth_actions",
    "predicted_actions",
    "num_ground_truth_actions",
    "num_predicted_actions",
    "correct",
    "unwanted_side_effects",
    "exact_match",
    "error",
    "no_actions",
    "wrong_email",
    "end_date_minor_error",
    "meeting_start_time_error",
]


def _revisited_sources() -> dict[str, str]:
    """Map results file (repo-relative posix path) -> model label for the published 2026 runs."""
    with open(MODEL_RESULTS_PATH) as f:
        models = json.load(f)["models"]
    return {source: label for label, entry in models.items() for source in entry["sources"].values()}


def _run_group(results_file: str, revisited_sources: dict[str, str]) -> str:
    if results_file in revisited_sources:
        return "revisited_2026"
    if not Path(meta_path_for_results(results_file)).exists():
        return "original_2024"
    return "other"


def _score_run(domain: str, results_path: Path, revisited_sources: dict[str, str]) -> pd.DataFrame:
    match = RESULTS_FILENAME.match(strip_results_suffix(results_path.name))
    if match is None:
        raise ValueError(f"Unexpected results filename {results_path.name!r} in {results_path.parent}.")
    results_file = results_path.relative_to(_ROOT).as_posix()
    version = ground_truth_version_for_results(results_file)
    gt_path = ground_truth_path(domain, version)
    df = load_and_score_results(results_file, gt_path)
    gt_index = {task: i for i, task in enumerate(pd.read_csv(gt_path, dtype=str)["task"])}

    df["run_group"] = _run_group(results_file, revisited_sources)
    df["model"] = match["model"]
    df["tool_selection"] = match["tool_selection"]
    df["run_timestamp"] = match["run_timestamp"]
    df["ground_truth_version"] = version
    df["results_file"] = results_file
    df["domain"] = domain
    df["task_id"] = [f"{domain}-{gt_index[task]:03d}" for task in df["task"]]
    df["task_domains"] = df["domains"]
    df["ground_truth_actions"] = df["ground_truth"].apply(repr)
    df["predicted_actions"] = df["prediction"].apply(repr)
    df["num_ground_truth_actions"] = df["ground_truth"].apply(len)
    df["num_predicted_actions"] = df["prediction"].apply(len)
    return df[COLUMNS]


def export_item_level_results() -> pd.DataFrame:
    revisited_sources = _revisited_sources()
    frames = []
    for domain in TOOLS:
        domain_dir = RESULTS_ROOT / domain
        for path in sorted(domain_dir.iterdir()):
            if path.name.endswith(RESULTS_SUFFIXES):
                frames.append(_score_run(domain, path, revisited_sources))
    df = pd.concat(frames, ignore_index=True)

    order = df.assign(
        _group=df["run_group"].map({"revisited_2026": 0, "original_2024": 1, "other": 2}),
        _domain=df["domain"].map({domain: i for i, domain in enumerate(TOOLS)}),
    ).sort_values(["_group", "model", "tool_selection", "_domain"], kind="stable")
    df = df.loc[order.index].reset_index(drop=True)
    _check(df, revisited_sources)
    return df


def _check(df: pd.DataFrame, revisited_sources: dict[str, str]) -> None:
    duplicates = df.duplicated(["results_file", "task_id"])
    assert not duplicates.any(), f"{duplicates.sum()} duplicate (results_file, task_id) rows"
    task_ids_per_domain = df.groupby("domain")["task_id"].nunique()
    rows_per_file = df.groupby(["domain", "results_file"]).size().reset_index(name="rows")
    for row in rows_per_file.itertuples():
        expected = task_ids_per_domain[row.domain]
        assert row.rows == expected, f"{row.results_file}: {row.rows} rows vs {expected} task ids"

    for key, run in df.groupby(["run_group", "model", "tool_selection"], sort=False):
        assert set(run["domain"]) == set(TOOLS), f"{key} covers domains {sorted(set(run['domain']))}"
        assert run["results_file"].nunique() == len(TOOLS), f"{key} has more than one results file per domain"

    with open(MODEL_RESULTS_PATH) as f:
        models = json.load(f)["models"]
    revisited = df[df["run_group"] == "revisited_2026"]
    assert set(revisited["results_file"]) == set(revisited_sources), (
        f"revisited_2026 rows do not cover exactly the sources in {MODEL_RESULTS_PATH.name}"
    )
    assert set(revisited["model"]) == set(RETRO_MODELS.values())
    for label, entry in models.items():
        model_rows = revisited[revisited["model"] == entry["model_name"]]
        assert len(model_rows) == entry["total"], f"{label}: {len(model_rows)} rows vs total {entry['total']}"
        for tool, expected in entry["per_tool"].items():
            tool_rows = model_rows[model_rows["domain"] == tool]
            actual = {
                "correct": int(tool_rows["correct"].sum()),
                "side_effects": int(tool_rows["unwanted_side_effects"].sum()),
                "total": len(tool_rows),
            }
            assert actual == expected, f"{label}/{tool}: item-level {actual} vs model_results.json {expected}"


def main() -> None:
    warnings.filterwarnings("ignore")
    df = export_item_level_results()
    df.to_csv(OUTPUT_PATH, index=False, compression={"method": "gzip", "mtime": 0})
    counts = df.groupby("run_group").agg(runs=("results_file", "nunique"), rows=("task", "size"))
    print(counts.to_string())
    print(f"Wrote {OUTPUT_PATH.relative_to(_ROOT)} with {len(df)} rows ({df['results_file'].nunique()} results files).")


if __name__ == "__main__":
    main()
