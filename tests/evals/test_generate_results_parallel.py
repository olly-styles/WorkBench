import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd

from src.evals.agent import AgentResult, Route
from src.evals.inference import generate_results
from src.tools.tool import Tool

_FAKE_ROUTE = Route("openai/gpt-4", "https://openrouter.ai/api/v1", "fake-key", "openrouter", True)


def _make_agent_result() -> AgentResult:
    return AgentResult(
        output="done",
        intermediate_steps=[("calendar.get_events", {"date": "2024-01-01"})],
    )


def _mock_run_agent(
    model_name: str,
    tools: list[Tool],
    task: str,
    datetime_prefix: str,
    temperature: float = 0,
    act_without_confirmation: bool = False,
):
    return _make_agent_result()


@patch("src.evals.inference.reset_state")
@patch("src.evals.inference.resolve_route", return_value=_FAKE_ROUTE)
@patch("src.evals.inference.run_agent", side_effect=_mock_run_agent)
def test_parallel_produces_same_results_as_sequential(
    _mock_agent: MagicMock, _mock_route: MagicMock, _mock_reset: MagicMock
):
    tasks = [f"task_{i}" for i in range(10)]
    df = pd.DataFrame({"task": tasks, "outcome": ["[]"] * 10})

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test_tasks_and_outcomes.csv")
        df.to_csv(csv_path, index=False)

        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        sequential = generate_results(csv_path, "gpt-4", workers=1)
        parallel = generate_results(csv_path, "gpt-4", workers=4)

        os.chdir(original_cwd)

    assert list(sequential["task"]) == tasks
    assert list(parallel["task"]) == tasks
    assert list(sequential["function_calls"]) == list(parallel["function_calls"])
    assert list(sequential["error"]) == list(parallel["error"])
