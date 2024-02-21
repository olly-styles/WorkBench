import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
random.seed(42)

from src.evals.utils import generate_all_queries_and_answers
from src.data_generation.data_generation_utils import get_natural_language_date, HARDCODED_CURRENT_TIME
from src.tools.analytics import METRICS, metric_naming_dict, ANALYTICS_DATA

dates = ANALYTICS_DATA["date_of_visit"].unique()

def page_views_plot_logic():
    date_min = random.choice(dates)
    date_max = HARDCODED_CURRENT_TIME.date()
    natural_language_date = get_natural_language_date(date_min)
    metric = random.choice(METRICS)
    natural_language_metric = metric_naming_dict[metric]
    answer = [
        f"""analytics.create_plot.func(time_min='{date_min}', time_max='{date_max}', value_to_plot='{metric}', plot_type='line')"""
    ]
    return {
        "natural_language_date": natural_language_date,
        "natural_language_metric": natural_language_metric,
        "answer": answer,
    }

ANALYTICS_TEMPLATES = [
    {
        "query": """Can you plot {natural_language_metric} since {natural_language_date}?""",
        "logic": page_views_plot_logic,
    },
    {
        "query": """Plot the distribution of {natural_language_metric} on {date}""",
    },
    {
        "query": """Can you plot the distribution of both {natural_language_metric_1} and {natural_language_metric_2} between {date_min} and {date_max}?""",
    },
    {
        "query": """How many {natural_language_metric} did we get from {date_min} to {date_max}?""",
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} at any time between {date_min} and {date_max}, plot it for me""",
    },
    {
        "query": """If {natural_language_metric} {fell_or_grew} by more than {threshold} from {date_min} to {date_max}, plot it alongside {natural_language_metric_2}""",
    },
    {
        "query": """Make a plot of the correlation between {natural_language_metric_1} and {natural_language_metric_2} with data from {date_min} to {date_max}""",
    },
    {
        "query": """If there's a {positive_or_negative} correlation between {natural_language_metric_1} and {natural_language_metric_2} since {date_min}, make a plot of it""",
    },
    {
        "query": """Can you plot the correlation between {natural_language_metric_1} and {natural_language_metric_2} since {date_min}?""",
    },
    {
        "query": """Make a bar chart comparing {natural_language_metric_1} and {natural_language_metric_2} since {date_min}""",
    }
]

max_queries_per_template = 1  # Limit the number of queries per template

if __name__ == "__main__":
    generated_queries_and_answers = generate_all_queries_and_answers(ANALYTICS_TEMPLATES, max_queries_per_template)
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/analytics_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
