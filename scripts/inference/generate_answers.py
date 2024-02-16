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

args = parser.parse_args()

if __name__ == "__main__":
    ground_truth = pd.read_csv(args.queries_path)
    ground_truth["answer"] = ground_truth["answer"].apply(ast.literal_eval)
    results = generate_results(args.queries_path, args.model_name)
    calculate_metrics(ground_truth, results)
