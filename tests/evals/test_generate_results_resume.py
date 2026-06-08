import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd

from src.evals.agent import AgentResult, Route
from src.evals.inference import generate_results
from src.tools.tool import Tool

_FAKE_ROUTE = Route("openai/gpt-4", "https://openrouter.ai/api/v1", "fake-key", "openrouter", True)


def _ok_result(task: str) -> AgentResult:
    return AgentResult(output=f"done:{task}", intermediate_steps=[("calendar.get_events", {"date": "2024-01-01"})])


@patch("src.evals.inference.reset_state")
@patch("src.evals.inference.resolve_route", return_value=_FAKE_ROUTE)
def test_resume_skips_succeeded_and_reruns_errored(_mock_route: MagicMock, _mock_reset: MagicMock):
    tasks = [f"task_{i}" for i in range(5)]
    df = pd.DataFrame({"task": tasks, "outcome": ["[]"] * 5})

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "calendar_tasks_and_outcomes.csv")
        df.to_csv(csv_path, index=False)

        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            call_counts: dict[str, int] = {t: 0 for t in tasks}

            def first_run(model_name: str, tools: list[Tool], task: str, datetime_prefix: str, **kw: object):
                call_counts[task] += 1
                if task in ("task_1", "task_3"):
                    raise RuntimeError("simulated rate_limit blip")
                return _ok_result(task)

            with patch("src.evals.inference.run_agent", side_effect=first_run):
                generate_results(csv_path, "gpt-4", workers=2, log_traces=True)

            results_dir = os.path.join(tmpdir, "data", "results", "calendar")
            files = [f for f in os.listdir(results_dir) if f.endswith(".csv")]
            assert len(files) == 1
            first_csv = os.path.join(results_dir, files[0])
            first = pd.read_csv(first_csv).fillna("")
            errored_tasks = set(first[first["error"] != ""]["task"])
            assert errored_tasks == {"task_1", "task_3"}

            def second_run(model_name: str, tools: list[Tool], task: str, datetime_prefix: str, **kw: object):
                call_counts[task] += 1
                return _ok_result(task)

            with patch("src.evals.inference.run_agent", side_effect=second_run):
                generate_results(csv_path, "gpt-4", workers=2, log_traces=True, resume=True)

            files_after = [f for f in os.listdir(results_dir) if f.endswith(".csv")]
            assert len(files_after) == 1, "resume must reuse the existing CSV, not create a new one"
            final_csv = os.path.join(results_dir, files_after[0])
            assert final_csv == first_csv

            final = pd.read_csv(final_csv).fillna("")
            assert list(final["task"]) == tasks
            assert set(final["error"].unique()) == {""}

            assert call_counts["task_0"] == 1
            assert call_counts["task_2"] == 1
            assert call_counts["task_4"] == 1
            assert call_counts["task_1"] == 2
            assert call_counts["task_3"] == 2

            meta_path = final_csv.replace(".csv", "_meta.json")
            with open(meta_path) as f:
                meta = json.load(f)
            assert meta["num_resumed_from_prior_run"] == 3
            assert meta["num_to_run_this_invocation"] == 2
            assert meta["finished_at"] is not None
        finally:
            os.chdir(cwd)
