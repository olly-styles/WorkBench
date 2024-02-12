import pandas as pd
import argparse
import sys
import os
import ast

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
from src.evals.utils import calculate_metrics


parser = argparse.ArgumentParser()
parser.add_argument(
    "--predictions_path",
    type=str,
    help="path to answers csv. By default this is stored in data/results/",
    required=True,
)
parser.add_argument(
    "--ground_truth_path",
    type=str,
    help="path to ground truth csv. By default this is stored in data/processed/",
    required=True,
)
args = parser.parse_args()

predictions = pd.read_csv(args.predictions_path)
ground_truth = pd.read_csv(args.ground_truth_path, dtype=str)
ground_truth["answer"] = ground_truth["answer"].apply(ast.literal_eval)
predictions["function_calls"] = predictions["function_calls"].apply(ast.literal_eval)
calculate_metrics(ground_truth, predictions)
