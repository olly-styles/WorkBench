import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
load_dotenv(_PROJECT_ROOT / ".env")

from src.evals.inference import AVAILABLE_LLMS, generate_results  # noqa: E402

DEFAULT_TASK_PATHS = [
    "data/processed/tasks_and_outcomes/email_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/calendar_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/analytics_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/project_management_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/customer_relationship_manager_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/multi_domain_tasks_and_outcomes.csv",
]

parser = argparse.ArgumentParser(description="Run inference for many (model, tool_selection, task file) combos.")
parser.add_argument(
    "--models",
    nargs="+",
    default=AVAILABLE_LLMS,
    help="model names to evaluate (default: every model in the registry)",
)
parser.add_argument(
    "--tool_selections",
    nargs="+",
    default=["all", "domains"],
    choices=["all", "domains"],
    help="tool selection modes to evaluate (default: both)",
)
parser.add_argument(
    "--task_paths",
    nargs="+",
    default=DEFAULT_TASK_PATHS,
    help="task-and-outcome CSVs to evaluate against (default: all six domains)",
)
parser.add_argument("--workers", type=int, default=64, help="parallel workers per (model, tool_selection, domain) run")
parser.add_argument("--log_traces", action="store_true", help="also save the full LLM trace as JSON")
parser.add_argument(
    "--act_without_confirmation",
    action="store_true",
    help="add system prompt suffix telling the model to act without asking the user to confirm",
)
parser.add_argument(
    "--structured_outputs",
    action="store_true",
    help="use native API tool calling instead of ReAct text parsing",
)
parser.add_argument(
    "--resume",
    action="store_true",
    help="resume the most recent matching run for each (domain, model, tool_selection)",
)


if __name__ == "__main__":
    args = parser.parse_args()
    for tool_selection in args.tool_selections:
        for model in args.models:
            for task_path in args.task_paths:
                print(f"\n=== model={model} tool_selection={tool_selection} tasks={task_path} ===")
                generate_results(
                    task_path,
                    model,
                    tool_selection,
                    workers=args.workers,
                    log_traces=args.log_traces,
                    act_without_confirmation=args.act_without_confirmation,
                    structured_outputs=args.structured_outputs,
                    resume=args.resume,
                )
