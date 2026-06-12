import json
import os
from pathlib import Path

import pytest

from src.evals.metrics import (
    CURRENT_GROUND_TRUTH_VERSION,
    get_latest_results_from_dir,
    get_latest_results_path,
    ground_truth_path,
    ground_truth_version_for_results,
)


def test_results_without_meta_sidecar_use_v1(tmp_path: Path):
    results = tmp_path / "gpt-4_all_2024-03-24_05-00-00.csv"
    results.write_text("task,function_calls,full_response,error\n")
    assert ground_truth_version_for_results(str(results)) == "v1"


def test_results_with_meta_sidecar_default_to_current_version(tmp_path: Path):
    results = tmp_path / "gpt-5.4_all_2026-06-04_05-00-00.csv"
    results.write_text("task,function_calls,full_response,error\n")
    (tmp_path / "gpt-5.4_all_2026-06-04_05-00-00_meta.json").write_text(json.dumps({"model_name": "gpt-5.4"}))
    assert ground_truth_version_for_results(str(results)) == CURRENT_GROUND_TRUTH_VERSION


def test_results_with_explicit_version_in_meta(tmp_path: Path):
    results = tmp_path / "gpt-5.4_all_2026-06-04_05-00-00.csv"
    results.write_text("task,function_calls,full_response,error\n")
    (tmp_path / "gpt-5.4_all_2026-06-04_05-00-00_meta.json").write_text(json.dumps({"ground_truth_version": "v1"}))
    assert ground_truth_version_for_results(str(results)) == "v1"


def test_ground_truth_path_current_is_top_level():
    path = ground_truth_path("calendar", CURRENT_GROUND_TRUTH_VERSION)
    assert path == os.path.join("data", "processed", "tasks_and_outcomes", "calendar_tasks_and_outcomes.csv")
    assert os.path.exists(path)


def test_ground_truth_path_v1_snapshot_exists_for_all_tools():
    for tool in [
        "calendar",
        "email",
        "analytics",
        "project_management",
        "customer_relationship_manager",
        "multi_domain",
    ]:
        path = ground_truth_path(tool, "v1")
        assert os.path.exists(path)


def test_ground_truth_path_unknown_version_raises():
    with pytest.raises(FileNotFoundError, match="v999"):
        ground_truth_path("calendar", "v999")


def test_get_latest_results_path_returns_versioned_ground_truth(tmp_path: Path):
    tool_dir = tmp_path / "calendar"
    tool_dir.mkdir()
    (tool_dir / "gpt-4_all_2024-03-24_05-00-00.csv").write_text("task,function_calls,full_response,error\n")
    result = get_latest_results_path(str(tmp_path), "gpt-4", "calendar", all_tools_in_prompt=True)
    assert result is not None
    assert result[1] == ground_truth_path("calendar", "v1")


def test_published_2024_gpt4_calendar_results_reproduce():
    summary = get_latest_results_from_dir("data/results", "gpt-4", "calendar", print_errors=False)
    assert summary is not None
    assert summary.num_correct + summary.num_incorrect == 110
    assert summary.num_correct == 71
    assert summary.num_side_effects == 24


@pytest.mark.parametrize("model", ["qwen-3.5-flash", "deepseek-v4-pro"])
@pytest.mark.parametrize(
    "tool",
    [
        "calendar",
        "email",
        "analytics",
        "project_management",
        "customer_relationship_manager",
        "multi_domain",
    ],
)
def test_may_2026_domains_runs_align_with_their_pinned_ground_truth(model: str, tool: str):
    import pandas as pd

    result = get_latest_results_path("data/results", model, tool, all_tools_in_prompt=False)
    assert result is not None
    results_path, gt_path = result
    predictions = pd.read_csv(results_path, dtype=str)
    ground_truth = pd.read_csv(gt_path, dtype=str)
    assert len(predictions) == len(ground_truth)
    assert set(predictions["task"]) == set(ground_truth["task"])
