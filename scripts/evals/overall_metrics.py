import os
import sys
import pandas as pd

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
from src.evals.utils import calculate_metrics


tools = ["sample"]
models = ["gpt-3.5-turbo-instruct", "gpt-4-0125-preview"]

results_root_dir = os.path.join("data", "results")
for tool in tools:
    for action in ["single", "multi"]:
        tool_results_dir = os.path.join(results_root_dir, tool, action)
        results_files = os.listdir(tool_results_dir)
        for model in models:
            model_results_files = [os.path.join(tool_results_dir, file) for file in results_files if model in file]
            latest_file = max(model_results_files) if len(model_results_files) > 0 else None
            if latest_file:
                predictions = pd.read_csv(latest_file)
                ground_truth = pd.read_csv(os.path.join("data", "processed", f"{tool}_questions_and_answers_{action}_action.csv"), dtype=str)
                calculate_metrics(ground_truth, predictions, print_errors=False)
            else:
                print(f"No results found for {model} in {tool} {action} action.")
