import os
import sys

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import generate_results

models = ["gpt-3.5-turbo-instruct", "gpt-4-0125-preview"]
queries_paths = [
    "data/processed/multi_domain_queries_and_answers.csv",
    "data/processed/email_queries_and_answers_single_action.csv",
    "data/processed/email_queries_and_answers_multi_action.csv",
    "data/processed/calendar_queries_and_answers_single_action.csv",
    "data/processed/calendar_queries_and_answers_multi_action.csv",
]

if __name__ == "__main__":
    for model in models:
        for queries_path in queries_paths:
            generate_results(queries_path, model)
