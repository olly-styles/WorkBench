import pandas as pd
import argparse
import warnings
import sys
import os
import ast

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import AVAILABLE_LLMS, generate_results, calculate_metrics

warnings.filterwarnings("ignore")  # suppress langchain deprecation warnings

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model_name",
    type=str,
    help="model name. Must be one of " + ", ".join(AVAILABLE_LLMS),
    required=True,
)
parser.add_argument(
    "--queries_path",
    type=str,
    help="path to queries and answers csv. By default these are stored in data/processed/queries_and_answers/",
    required=True,
)

parser.add_argument(
    "--toolkits",
    action="append",
    nargs="*",
    help="toolkits to be used for generating answers. By default all toolkits are used: 'email', 'calendar', 'analytics', 'project_management', 'customer_relationship_manager'",
    default=[],
)

parser.add_argument(
    "--tool_selection",
    type=str,
    help="tool selection method. Must be one of 'all', 'domains', 'oracle'",
    default='all'
)

args = parser.parse_args()

if not args.toolkits:
    args.toolkits = [
        [
            "email",
            "calendar",
            "analytics",
            "project_management",
            "customer_relationship_manager",
        ]
    ]

if __name__ == "__main__":
    ground_truth = pd.read_csv(args.queries_path)
    ground_truth["answer"] = ground_truth["answer"].apply(ast.literal_eval)
    results = generate_results(args.queries_path, args.model_name, args.toolkits[0], args.tool_selection)
    calculate_metrics(ground_truth, results)
