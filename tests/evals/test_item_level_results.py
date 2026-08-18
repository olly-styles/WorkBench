import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.evals.export_item_level_results import COLUMNS, OUTPUT_PATH, RESULTS_ROOT, TOOLS
from src.evals.metrics import RESULTS_SUFFIXES, get_latest_results_from_dir

MODEL_RESULTS_PATH = Path("retro/data/model_results.json")


@pytest.fixture(scope="module")
def item_level() -> pd.DataFrame:
    return pd.read_csv(OUTPUT_PATH)


def test_artifact_has_expected_columns_and_no_duplicates(item_level: pd.DataFrame):
    assert list(item_level.columns) == COLUMNS
    assert not item_level.duplicated(["results_file", "task_id"]).any()
    assert item_level["correct"].dtype == bool
    assert item_level["unwanted_side_effects"].dtype == bool
    assert set(item_level["run_group"]) == {"revisited_2026", "original_2024", "other"}


def test_artifact_covers_every_committed_results_file(item_level: pd.DataFrame):
    committed = {
        path.relative_to(RESULTS_ROOT.parents[1]).as_posix()
        for domain in TOOLS
        for path in (RESULTS_ROOT / domain).iterdir()
        if path.name.endswith(RESULTS_SUFFIXES)
    }
    assert set(item_level["results_file"]) == committed
    rows_per_file = item_level.groupby(["domain", "results_file"]).size().reset_index(name="rows")
    task_ids_per_domain = item_level.groupby("domain")["task_id"].nunique()
    for row in rows_per_file.itertuples():
        expected = task_ids_per_domain[row.domain]
        assert row.rows == expected, f"{row.results_file}: {row.rows} rows vs {expected} task ids"
    assert task_ids_per_domain.sum() == 690


def test_task_id_is_stable_across_ground_truth_versions(item_level: pd.DataFrame):
    by_version = item_level.groupby(["ground_truth_version", "task_id"])["task"].nunique()
    assert (by_version == 1).all()
    v1 = item_level[item_level["ground_truth_version"] == "v1"].drop_duplicates("task_id").set_index("task_id")
    v2 = item_level[item_level["ground_truth_version"] == "v2"].drop_duplicates("task_id").set_index("task_id")
    assert set(v1.index) == set(v2.index)
    assert (v1["task"] != v2.loc[v1.index, "task"]).sum() == 56


def test_revisited_rows_reproduce_model_results_json(item_level: pd.DataFrame):
    with open(MODEL_RESULTS_PATH) as f:
        models = json.load(f)["models"]
    revisited = item_level[item_level["run_group"] == "revisited_2026"]
    assert set(revisited["results_file"]) == {s for m in models.values() for s in m["sources"].values()}
    for label, entry in models.items():
        rows = revisited[revisited["model"] == entry["model_name"]]
        assert len(rows) == entry["total"], label
        assert int(rows["correct"].sum()) == entry["correct"], label
        assert int(rows["unwanted_side_effects"].sum()) == entry["side_effects"], label
        for tool, expected in entry["per_tool"].items():
            tool_rows = rows[rows["domain"] == tool]
            assert int(tool_rows["correct"].sum()) == expected["correct"], f"{label}/{tool}"
            assert int(tool_rows["unwanted_side_effects"].sum()) == expected["side_effects"], f"{label}/{tool}"


def test_original_2024_rows_use_v1_ground_truth_and_match_recomputation(item_level: pd.DataFrame):
    original = item_level[item_level["run_group"] == "original_2024"]
    assert (original["ground_truth_version"] == "v1").all()
    assert original["run_timestamp"].str.startswith("2024-").all()
    gpt4 = original[(original["model"] == "gpt-4") & (original["tool_selection"] == "all")]
    assert len(gpt4) == 690
    summary = get_latest_results_from_dir("data/results", "gpt-4", "calendar", print_errors=False)
    assert summary is not None
    calendar = gpt4[gpt4["domain"] == "calendar"]
    assert int(calendar["correct"].sum()) == summary.num_correct
    assert int(calendar["unwanted_side_effects"].sum()) == summary.num_side_effects


def test_side_effects_only_flagged_on_incorrect_rows(item_level: pd.DataFrame):
    assert not (item_level["correct"] & item_level["unwanted_side_effects"]).any()
