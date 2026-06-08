import os
from pathlib import Path

from src.evals.metrics import get_latest_results_path


def _touch(path: Path):
    path.write_text("task,function_calls,full_response,error\n")


def test_picks_latest_by_timestamp_not_filesystem_ctime(tmp_path: Path):
    tool_dir = tmp_path / "calendar"
    tool_dir.mkdir()
    _touch(tool_dir / "gpt-4_all_2024-03-24_05-00-00.csv")
    _touch(tool_dir / "gpt-4_all_2024-03-23_05-00-00.csv")
    result = get_latest_results_path(str(tmp_path), "gpt-4", "calendar", all_tools_in_prompt=True)
    assert result is not None
    assert os.path.basename(result[0]) == "gpt-4_all_2024-03-24_05-00-00.csv"


def test_matches_model_exactly_not_as_substring(tmp_path: Path):
    tool_dir = tmp_path / "calendar"
    tool_dir.mkdir()
    _touch(tool_dir / "gpt-3.5_domains_2024-03-24_05-00-00.csv")
    assert get_latest_results_path(str(tmp_path), "gpt-3", "calendar", all_tools_in_prompt=False) is None
    assert get_latest_results_path(str(tmp_path), "gpt-3.5", "calendar", all_tools_in_prompt=False) is not None


def test_respects_tool_selection(tmp_path: Path):
    tool_dir = tmp_path / "calendar"
    tool_dir.mkdir()
    _touch(tool_dir / "gpt-4_all_2024-03-24_05-00-00.csv")
    _touch(tool_dir / "gpt-4_domains_2024-03-25_05-00-00.csv")
    all_result = get_latest_results_path(str(tmp_path), "gpt-4", "calendar", all_tools_in_prompt=True)
    domains_result = get_latest_results_path(str(tmp_path), "gpt-4", "calendar", all_tools_in_prompt=False)
    assert all_result is not None
    assert domains_result is not None
    assert os.path.basename(all_result[0]) == "gpt-4_all_2024-03-24_05-00-00.csv"
    assert os.path.basename(domains_result[0]) == "gpt-4_domains_2024-03-25_05-00-00.csv"


def test_returns_none_when_no_matching_file(tmp_path: Path):
    (tmp_path / "calendar").mkdir()
    assert get_latest_results_path(str(tmp_path), "gpt-4", "calendar", all_tools_in_prompt=True) is None
