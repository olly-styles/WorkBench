import os
import sys
import argparse

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
from src.evals.utils import AVAILABLE_LLMS, get_latest_results_from_dir

results_root_dir = os.path.join("data", "results")
full_tools_list = [
    "multi_domain",
    "email",
    "calendar",
    "analytics",
    "project_management",
    "customer_relationship_manager",
]


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    "--tools",
    action="append",
    default=[],
    help=f"Call with --tools <tool 1> --tools <tool 2> etc. Defaults to {full_tools_list}.",
)
arg_parser.add_argument(
    "--models",
    action="append",
    default=[],
    help=f"Call with --models <model 1> --models <model 2> etc. Defaults to {AVAILABLE_LLMS}.",
)
arg_parser.add_argument(
    "--print_errors",
    action="store_true",
    help="Print errors when calculating metrics.",
    default=False,
)
args = arg_parser.parse_args()

if __name__ == "__main__":
    tools = args.tools if len(args.tools) else full_tools_list
    models = args.models if len(args.models) else AVAILABLE_LLMS
    for tool in tools:
        get_latest_results_from_dir(results_root_dir, tool, models, args.print_errors)
