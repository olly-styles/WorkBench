import os
import sys
import argparse

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
from src.evals.utils import get_latest_results_from_dir

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--tools", action="append", default=[], help="Call with --tools <tool 1> --tools <tool 2> defaults to all tools.")
arg_parser.add_argument("--models", action="append", default=[], help="Call with --models <model 1> --models <model 2> defaults to all models.")
args = arg_parser.parse_args()

results_root_dir = os.path.join("data", "results")
full_tools_list = ["multi_domain", "calendar", "email"]
full_models_list = ["gpt-3.5-turbo-instruct", "gpt-4-0125-preview"]

if __name__ == "__main__":
    tools = args.tools if len(args.tools) else full_tools_list
    models = args.models if len(args.models) else full_models_list
    for tool in tools:
        for action in ["single", "multi"]:
            get_latest_results_from_dir(results_root_dir, tool, action, models)