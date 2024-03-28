import os
import sys

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import AVAILABLE_LLMS, generate_results

models = AVAILABLE_LLMS

query_paths = [
    "data/processed/queries_and_answers/email_queries_and_answers.csv",
    "data/processed/queries_and_answers/calendar_queries_and_answers.csv",
    "data/processed/queries_and_answers/analytics_queries_and_answers.csv",
    "data/processed/queries_and_answers/project_management_queries_and_answers.csv",
    "data/processed/queries_and_answers/customer_relationship_manager_queries_and_answers.csv",
    "data/processed/queries_and_answers/multi_domain_queries_and_answers.csv",
]

if __name__ == "__main__":
    for tool_selection in ["all", "domains"]:
        for model in models:
            for query_path in query_paths:
                generate_results(query_path, model, tool_selection)
