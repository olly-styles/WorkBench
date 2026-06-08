import argparse
import ast
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
load_dotenv(_PROJECT_ROOT / ".env")

from src.evals.inference import AVAILABLE_LLMS, generate_results  # noqa: E402
from src.evals.metrics import calculate_metrics  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model_name",
    type=str,
    help="model name. Must be one of " + ", ".join(AVAILABLE_LLMS),
    required=True,
)
parser.add_argument(
    "--tasks_path",
    type=str,
    help="path to tasks and outcomes csv. By default these are stored in data/processed/tasks_and_outcomes/",
    required=True,
)

parser.add_argument(
    "--tool_selection", type=str, help="tool selection method. Must be one of 'all', 'domains'", default="all"
)

parser.add_argument("--workers", type=int, help="number of parallel workers for task execution", default=64)

parser.add_argument(
    "--log_traces", action="store_true", help="save full LLM traces (inputs, outputs, observations) as JSON"
)

parser.add_argument(
    "--act_without_confirmation",
    action="store_true",
    help="add system prompt suffix instructing the model to act without asking for confirmation",
)

parser.add_argument(
    "--structured_outputs",
    action="store_true",
    help="use native API tool calling instead of ReAct text parsing",
)

parser.add_argument(
    "--resume",
    action="store_true",
    help="resume the most recent matching run for this (domain, model, tool_selection): "
    "keep rows with empty error and only re-run missing/errored tasks",
)

if __name__ == "__main__":
    args = parser.parse_args()
    ground_truth = pd.read_csv(args.tasks_path)
    ground_truth["outcome"] = ground_truth["outcome"].apply(ast.literal_eval)
    results = generate_results(
        args.tasks_path,
        args.model_name,
        args.tool_selection,
        workers=args.workers,
        log_traces=args.log_traces,
        act_without_confirmation=args.act_without_confirmation,
        structured_outputs=args.structured_outputs,
        resume=args.resume,
    )
    calculate_metrics(ground_truth, results)
