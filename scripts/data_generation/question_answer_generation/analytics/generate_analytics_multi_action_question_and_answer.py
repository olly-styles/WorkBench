import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
random.seed(42)

from src.evals.utils import generate_all_questions_and_answers
from src.data_generation.data_generation_utils import get_natural_language_date

def page_views_plot_logic():
    time_min = "2023-10-01"
    time_max = "2023-10-31"
    date_min = get_natural_language_date(time_min)
    date_max = get_natural_language_date(time_max)
    return {"time_min": time_min, "time_max": time_max, "date_min": date_min, "date_max": date_max}

MULTI_ACTION_TEMPLATES = [
    {
        "question": "Make a plot of page views from {date_min} to {date_max}",
        "answer": [
            """analytics.create_plot.func(time_min='{time_min}', time_max='{time_max}', value_to_plot='page_views', plot_type='line')"""
        ],
        "logic": page_views_plot_logic
    },
]

max_questions_per_template = 1  # Limit the number of questions per template

if __name__ == "__main__":
    generated_questions_and_answers = generate_all_questions_and_answers(MULTI_ACTION_TEMPLATES, max_questions_per_template)
    df = pd.DataFrame(generated_questions_and_answers)
    df.to_csv(
        "data/processed/analytics_questions_and_answers_multi_action.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
