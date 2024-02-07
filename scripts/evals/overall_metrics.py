import os
import sys
import argparse

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
from src.evals.utils import get_latest_results_from_dir

results_root_dir = os.path.join("data", "results")
full_tools_list = ["multi_domain", "calendar", "email"]
full_models_list = ["gpt-3.5-turbo-instruct", "gpt-4-0125-preview"]

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    "--tools",
    action="append",
    default=full_tools_list,
    help=f"Call with --tools <tool 1> --tools <tool 2> etc. Defaults to {full_tools_list}.",
)
arg_parser.add_argument(
    "--models",
    action="append",
    default=full_models_list,
    help=f"Call with --models <model 1> --models <model 2> etc. Defaults to {full_models_list}.",
)
arg_parser.add_argument(
    "--print_errors",
    action="store_true",
    help="Print errors when calculating metrics.",
    default=False,
)
args = arg_parser.parse_args()

if __name__ == "__main__":
    for tool in args.tools:
        for action in ["single", "multi"]:
            if action == "single" and tool == "multi_domain":
                continue
            get_latest_results_from_dir(
                results_root_dir, tool, action, args.models, args.print_errors
            )
