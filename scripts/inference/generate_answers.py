import pandas as pd
import argparse
import warnings
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import generate_results, calculate_metrics

warnings.filterwarnings("ignore")  # supress langchain deprication warnings

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model_name",
    type=str,
    help="model name, either gpt-3.5-turbo-instruct or gpt-4-0125-preview",
    required=True,
)
parser.add_argument(
    "--questions_path",
    type=str,
    help="path to questions and answers csv. By default this is stored in data/processed/",
    required=True,
)

args = parser.parse_args()

if __name__ == "__main__":
    ground_truth = pd.read_csv(args.questions_path)
    results = generate_results(args.questions_path, args.model_name)
    calculate_metrics(ground_truth, results)
