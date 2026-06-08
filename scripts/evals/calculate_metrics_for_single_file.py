import argparse
import ast

import pandas as pd

from src.evals.metrics import calculate_metrics

parser = argparse.ArgumentParser()
parser.add_argument(
    "--predictions_path",
    type=str,
    help="path to outcomes csv. By default this is stored in data/results/",
    required=True,
)
parser.add_argument(
    "--ground_truth_path",
    type=str,
    help="path to ground truth csv. By default this is stored in data/processed/",
    required=True,
)
if __name__ == "__main__":
    args = parser.parse_args()
    predictions = pd.read_csv(args.predictions_path, engine="python", on_bad_lines="warn")
    ground_truth = pd.read_csv(args.ground_truth_path, dtype=str)
    ground_truth["outcome"] = ground_truth["outcome"].apply(ast.literal_eval)
    predictions["function_calls"] = predictions["function_calls"].apply(ast.literal_eval)
    calculate_metrics(ground_truth, predictions)
