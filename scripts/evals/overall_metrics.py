import os
import sys
import pandas as pd

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
from src.evals.utils import get_latest_results_from_dir

tools = ["calendar", "email"]
models = ["gpt-3.5-turbo-instruct", "gpt-4-0125-preview"]
results_root_dir = os.path.join("data", "results")

if __name__ == "__main__":
    for tool in tools:
        for action in ["single", "multi"]:
            get_latest_results_from_dir(results_root_dir, tool, action, models)