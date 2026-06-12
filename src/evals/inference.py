import ast
import csv
import glob
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

import openai
import pandas as pd

from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME
from src.evals.actions import convert_intermediate_step_to_function_call
from src.evals.agent import (
    AGENT_STOPPED_MESSAGE,
    MODEL_REGISTRY,
    AgentResult,
    Route,
    build_system_prompt,
    resolve_route,
    run_agent,
    run_agent_structured,
)
from src.evals.metrics import CURRENT_GROUND_TRUTH_VERSION
from src.tools.state import reset_state
from src.tools.tool import Tool
from src.tools.toolkits import (
    analytics_toolkit,
    calendar_toolkit,
    company_directory_toolkit,
    customer_relationship_manager_toolkit,
    email_toolkit,
    project_management_toolkit,
)

logger = logging.getLogger(__name__)

AVAILABLE_LLMS = list(MODEL_REGISTRY.keys())


_TOOLKIT_MAP: dict[str, list[Tool]] = {
    "email": email_toolkit,
    "calendar": calendar_toolkit,
    "analytics": analytics_toolkit,
    "project_management": project_management_toolkit,
    "customer_relationship_manager": customer_relationship_manager_toolkit,
}


def get_toolkits(toolkits: list[str]) -> list[Tool]:
    """Get the toolkits to be used for the agent."""
    tools: list[Tool] = []
    for name in toolkits:
        if name in _TOOLKIT_MAP:
            tools += _TOOLKIT_MAP[name]
    # The company directory toolkit is always included in order to find email addresses by name
    tools += company_directory_toolkit
    return tools


def _collect_result(result: AgentResult, function_calls: list[str], all_traces: list[dict]) -> None:
    all_traces.extend(asdict(s) for s in result.trace)
    for tool_name, tool_input in result.intermediate_steps:
        function_calls.append(convert_intermediate_step_to_function_call(tool_name, tool_input))


# APIs for the LLMs we support have different error messages for when the context window is exceeded
_CONTEXT_WINDOW_MESSAGE_PATTERNS = (
    "maximum input length",
    "maximum context length",
    "prompt is too long",
    "request too large",
    "context_length_exceeded",
)


def _is_context_window_error(exc: Exception) -> bool:
    if isinstance(exc, openai.BadRequestError):
        code = getattr(exc, "code", None)
        if code and "context" in str(code).lower():
            return True
    return any(pattern in str(exc).lower() for pattern in _CONTEXT_WINDOW_MESSAGE_PATTERNS)


def _run_single_task(
    index: int,
    task: str,
    model_name: str,
    tools: list[Tool],
    datetime_prefix: str,
    act_without_confirmation: bool = False,
    structured_outputs: bool = False,
) -> dict[str, object]:
    task_start = time.time()
    error = ""
    function_calls: list[str] = []
    response: AgentResult | str = ""
    all_traces: list[dict] = []
    agent_fn = run_agent_structured if structured_outputs else run_agent
    try:
        result = agent_fn(
            model_name,
            tools,
            task,
            datetime_prefix,
            temperature=0,
            act_without_confirmation=act_without_confirmation,
        )
        response = result
        _collect_result(result, function_calls, all_traces)
        if result.output == AGENT_STOPPED_MESSAGE:
            error = result.output

    except Exception as e:
        if _is_context_window_error(e):
            logger.warning("Context window exceeded with task: %s", task)
            error = "Context window exceeded"
        else:
            logger.exception("Unexpected error with task: %s", task)
            error = str(e)

    elapsed = time.time() - task_start
    num_steps = len(all_traces)
    print(f"### Task: {task}")
    print(f"### Outcome: {function_calls}")
    print(f"### Steps: {num_steps} | Time: {elapsed:.1f}s | Error: {error or 'none'}")

    reset_state()

    return {
        "task": task,
        "function_calls": function_calls,
        "full_response": str(response),
        "error": error,
        "trace": all_traces,
        "_index": index,
    }


def _save_progress(
    row_dicts: list[dict],
    save_path: str,
    log_traces: bool,
) -> None:
    sorted_rows = sorted(row_dicts, key=lambda d: d["_index"])
    traces = [d["trace"] for d in sorted_rows]
    csv_rows = [{k: v for k, v in d.items() if k not in ("_index", "trace")} for d in sorted_rows]
    results = pd.DataFrame(csv_rows, columns=pd.Index(["task", "function_calls", "full_response", "error"]))
    results.to_csv(save_path, index=False, quoting=csv.QUOTE_ALL)
    if log_traces:
        trace_data = [{"task": d["task"], "steps": t} for d, t in zip(sorted_rows, traces)]
        trace_path = save_path.replace(".csv", "_traces.json")
        with open(trace_path, "w") as f:
            json.dump(trace_data, f, indent=2)


def _find_latest_results_path(save_dir: str, model_name: str, tool_selection: str) -> str | None:
    pattern = os.path.join(save_dir, f"{model_name}_{tool_selection}_*.csv")
    matches = glob.glob(pattern)
    if not matches:
        return None
    return max(matches)


def _load_existing_progress(save_path: str, tasks: list[str], log_traces: bool) -> tuple[list[dict], set[int]]:
    """Load prior results from `save_path` and return (rows_to_keep, indices_to_skip).

    A task is skipped iff a matching row exists with an empty error field. Errored or
    missing tasks are re-run by the caller.
    """
    if not os.path.exists(save_path):
        return [], set()

    prior = pd.read_csv(save_path, dtype=str).fillna("")
    by_task: dict[str, dict] = {str(r["task"]): r.to_dict() for _, r in prior.iterrows()}

    trace_by_task: dict[str, list[dict]] = {}
    if log_traces:
        trace_path = save_path.replace(".csv", "_traces.json")
        if os.path.exists(trace_path):
            with open(trace_path) as f:
                for entry in json.load(f):
                    trace_by_task[entry["task"]] = entry.get("steps", [])

    rows: list[dict] = []
    skip: set[int] = set()
    for i, task in enumerate(tasks):
        row = by_task.get(task)
        if row is None or row.get("error", ""):
            continue
        rows.append(
            {
                "task": task,
                "function_calls": row.get("function_calls", ""),
                "full_response": row.get("full_response", ""),
                "error": "",
                "trace": trace_by_task.get(task, []),
                "_index": i,
            }
        )
        skip.add(i)
    return rows, skip


def _write_run_metadata(
    save_path: str,
    *,
    model_name: str,
    route: Route,
    tool_selection: str,
    tasks_path: str,
    num_tasks: int,
    num_to_run: int,
    num_resumed: int,
    workers: int,
    log_traces: bool,
    act_without_confirmation: bool,
    structured_outputs: bool,
    datetime_prefix: str,
    sample_system_prompt: str,
    started_at: str,
    finished_at: str | None = None,
) -> None:
    meta = {
        "model_name": model_name,
        "model_id": route.model_id,
        "provider": route.provider,
        "base_url": route.base_url,
        "supports_temperature": route.supports_temperature,
        "tool_selection": tool_selection,
        "tasks_path": tasks_path,
        "ground_truth_version": CURRENT_GROUND_TRUTH_VERSION,
        "num_tasks": num_tasks,
        "num_to_run_this_invocation": num_to_run,
        "num_resumed_from_prior_run": num_resumed,
        "workers": workers,
        "log_traces": log_traces,
        "act_without_confirmation": act_without_confirmation,
        "structured_outputs": structured_outputs,
        "datetime_prefix": datetime_prefix,
        "sample_system_prompt": sample_system_prompt,
        "started_at": started_at,
        "finished_at": finished_at,
    }
    meta_path = save_path.replace(".csv", "_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)


def generate_results(
    tasks_path: str,
    model_name: str,
    tool_selection: str = "all",
    workers: int = 1,
    log_traces: bool = False,
    act_without_confirmation: bool = False,
    structured_outputs: bool = False,
    resume: bool = False,
) -> pd.DataFrame:
    """Generates results for a given model and set of tasks. Saves the results to a csv file.

    When ``resume`` is True, reuses the most recent matching results CSV for
    (domain, model, tool_selection): rows with an empty ``error`` are kept verbatim,
    and only missing / errored tasks are re-run.
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError("Invalid --model_name. Must be one of " + ", ".join(AVAILABLE_LLMS))

    tasks_df = pd.read_csv(tasks_path)
    tasks = tasks_df["task"].tolist()

    route = resolve_route(model_name)
    print(f"Routing '{model_name}' to {route.provider} ({route.base_url}) as model id '{route.model_id}'")
    datetime_prefix = (
        f"Today's date is {HARDCODED_CURRENT_TIME.strftime('%A')}, {HARDCODED_CURRENT_TIME.date()} "
        f"and the current time is {HARDCODED_CURRENT_TIME.time()}. "
        f"Remember the current date and time when completing tasks. "
        f"Meetings must not start before 9am or end after 6pm."
    )

    if tool_selection == "domains":
        per_task_tools = [get_toolkits(ast.literal_eval(domains)) for domains in tasks_df["domains"]]
    else:
        default_tools = get_toolkits(list(_TOOLKIT_MAP))
        per_task_tools = [default_tools] * len(tasks)

    domain = tasks_path.split("/")[-1].split(".")[0].replace("_tasks_and_outcomes", "")
    save_dir = os.path.join("data", "results", domain)
    os.makedirs(save_dir, exist_ok=True)

    save_path: str | None = None
    row_dicts: list[dict] = []
    skip_indices: set[int] = set()
    if resume:
        existing = _find_latest_results_path(save_dir, model_name, tool_selection)
        if existing is not None:
            save_path = existing
            row_dicts, skip_indices = _load_existing_progress(save_path, tasks, log_traces)
            print(
                f"Resuming from {save_path}: "
                f"{len(skip_indices)}/{len(tasks)} tasks already succeeded, "
                f"{len(tasks) - len(skip_indices)} to (re)run."
            )

    if save_path is None:
        # Removes microseconds and makes it more readable
        current_datetime = str(pd.Timestamp.now()).split(".")[0].replace(" ", "_").replace(":", "-")
        save_path = os.path.join(save_dir, model_name + "_" + tool_selection + "_" + current_datetime + ".csv")

    sample_system_prompt = build_system_prompt(per_task_tools[0], datetime_prefix, act_without_confirmation)
    started_at = pd.Timestamp.now().isoformat()
    num_to_run = len(tasks) - len(skip_indices)
    _write_run_metadata(
        save_path,
        model_name=model_name,
        route=route,
        tool_selection=tool_selection,
        tasks_path=tasks_path,
        num_tasks=len(tasks),
        num_to_run=num_to_run,
        num_resumed=len(skip_indices),
        workers=workers,
        log_traces=log_traces,
        act_without_confirmation=act_without_confirmation,
        structured_outputs=structured_outputs,
        datetime_prefix=datetime_prefix,
        sample_system_prompt=sample_system_prompt,
        started_at=started_at,
    )

    pending = [(i, task) for i, task in enumerate(tasks) if i not in skip_indices]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                _run_single_task,
                i,
                task,
                model_name,
                per_task_tools[i],
                datetime_prefix,
                act_without_confirmation,
                structured_outputs,
            )
            for i, task in pending
        ]
        for future in as_completed(futures):
            row_dicts.append(future.result())
            print(f"Progress: {len(row_dicts)}/{len(tasks)}")
            _save_progress(row_dicts, save_path, log_traces)

    if log_traces:
        trace_path = save_path.replace(".csv", "_traces.json")
        print(f"Traces saved to {trace_path}")

    _write_run_metadata(
        save_path,
        model_name=model_name,
        route=route,
        tool_selection=tool_selection,
        tasks_path=tasks_path,
        num_tasks=len(tasks),
        num_to_run=num_to_run,
        num_resumed=len(skip_indices),
        workers=workers,
        log_traces=log_traces,
        act_without_confirmation=act_without_confirmation,
        structured_outputs=structured_outputs,
        datetime_prefix=datetime_prefix,
        sample_system_prompt=sample_system_prompt,
        started_at=started_at,
        finished_at=pd.Timestamp.now().isoformat(),
    )

    sorted_rows = sorted(row_dicts, key=lambda d: d["_index"])
    for d in sorted_rows:
        del d["_index"]
        del d["trace"]
    return pd.DataFrame(sorted_rows, columns=pd.Index(["task", "function_calls", "full_response", "error"]))
