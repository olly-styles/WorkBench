import os
import sys

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import generate_results

models = ["gpt-3.5-turbo-instruct", "gpt-4-0125-preview"]
questions_paths = [
    "data/processed/multi_domain_questions_and_answers.csv",
    "data/processed/email_questions_and_answers_single_action.csv",
    "data/processed/email_questions_and_answers_multi_action.csv",
    "data/processed/calendar_questions_and_answers_single_action.csv",
    "data/processed/calendar_questions_and_answers_multi_action.csv",
]

if __name__ == "__main__":
    for model in models:
        for questions_path in questions_paths:
            generate_results(questions_path, model)
