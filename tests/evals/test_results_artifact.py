import gzip
import json
from pathlib import Path

import pytest

from src.evals.metrics import (
    get_latest_results_path,
    meta_path_for_results,
    strip_results_suffix,
)

ARTIFACT_PATH = Path("retro/data/model_results.json")
TOOLS = [
    "calendar",
    "email",
    "analytics",
    "project_management",
    "customer_relationship_manager",
    "multi_domain",
]


def test_strip_results_suffix():
    assert strip_results_suffix("a_all_2026-06-03_14-12-16.csv") == "a_all_2026-06-03_14-12-16"
    assert strip_results_suffix("a_all_2026-06-03_14-12-16.csv.gz") == "a_all_2026-06-03_14-12-16"
    with pytest.raises(ValueError, match="not a results file"):
        strip_results_suffix("a_meta.json")


def test_meta_path_for_results_handles_gzip():
    assert meta_path_for_results("dir/run.csv") == "dir/run_meta.json"
    assert meta_path_for_results("dir/run.csv.gz") == "dir/run_meta.json"


def test_get_latest_results_path_picks_gzipped_files(tmp_path: Path):
    tool_dir = tmp_path / "calendar"
    tool_dir.mkdir()
    with gzip.open(tool_dir / "gpt-9_all_2026-06-05_05-00-00.csv.gz", "wt") as f:
        f.write("task,function_calls,full_response,error\n")
    (tool_dir / "gpt-9_all_2026-06-04_05-00-00.csv").write_text("task,function_calls,full_response,error\n")
    result = get_latest_results_path(str(tmp_path), "gpt-9", "calendar", all_tools_in_prompt=True)
    assert result is not None
    assert result[0].endswith("gpt-9_all_2026-06-05_05-00-00.csv.gz")


def test_artifact_is_committed_and_well_formed():
    with open(ARTIFACT_PATH) as f:
        payload = json.load(f)
    assert payload["total_tasks"] == 690
    models = payload["models"]
    assert len(models) == 24
    for label, entry in models.items():
        assert entry["total"] == 690, f"{label} has {entry['total']} tasks"
        assert 0 <= entry["correct"] <= entry["total"]
        assert 0 <= entry["side_effects"] <= entry["total"]
        assert set(entry["per_tool"]) == set(TOOLS)
        assert entry["correct"] == sum(t["correct"] for t in entry["per_tool"].values())
        assert entry["side_effects"] == sum(t["side_effects"] for t in entry["per_tool"].values())
        for tool, source in entry["sources"].items():
            assert Path(source).exists(), f"{label} {tool} source {source} missing"


def test_artifact_matches_recomputation_for_sample_model():
    from src.evals.metrics import get_latest_results_from_dir

    with open(ARTIFACT_PATH) as f:
        artifact = json.load(f)["models"]["Opus 4.8"]
    summary = get_latest_results_from_dir("data/results", "claude-opus-4.8", "calendar", print_errors=False)
    assert summary is not None
    assert artifact["per_tool"]["calendar"] == {
        "correct": summary.num_correct,
        "side_effects": summary.num_side_effects,
        "total": summary.num_correct + summary.num_incorrect,
    }
