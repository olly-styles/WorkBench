import pandas as pd
import numpy as np
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
random.seed(42)

from src.evals.utils import generate_all_queries_and_answers
from src.data_generation.data_generation_utils import get_natural_language_date, HARDCODED_CURRENT_TIME
from src.tools import analytics
from src.tools.analytics import METRICS, METRIC_NAMES, ANALYTICS_DATA

dates = ANALYTICS_DATA["date_of_visit"].unique()
metric_naming_dict = {metric: name for metric, name in zip(METRICS, METRIC_NAMES)}
metric_to_func_dict = {
    "page_views": analytics.total_visits_count,
    "session_duration_seconds": analytics.get_average_session_duration,
    "traffic_source": analytics.traffic_source_count,
    "user_engaged": analytics.engaged_users_count
}

def get_plot_string(metric, date_min, date_max, plot_type):
    return f"""analytics.create_plot.func(time_min='{date_min}', time_max='{date_max}', value_to_plot='{metric}', plot_type='{plot_type}')"""

def get_random_dict():
    date_min = random.choice(dates)
    metric = random.choice(METRICS)
    more_or_less = random.choice(["more", "less"])
    fell_or_grew = random.choice(["fell", "grew"])
    threshold = get_threshold(metric)
    return {
        "date_min": date_min,
        "date_max": str(HARDCODED_CURRENT_TIME.date()),
        "metric": metric,
        "natural_language_date": get_natural_language_date(date_min),
        "natural_language_metric": metric_naming_dict[metric],
        "plot_type": random.choice(["line", "bar", "scatter", "histogram"]),
        "more_or_less": more_or_less,
        "threshold": threshold,
        "fell_or_grew": fell_or_grew,
    }

def get_threshold(metric):
    """Gets the threshold for a given metric over the whole time series"""
    data = ANALYTICS_DATA[["date_of_visit", metric]]
    data[metric] = data[metric].astype(float)
    threshold_percentage = random.randint(1, 99)
    threshold = np.percentile(data.groupby("date_of_visit").mean(), threshold_percentage)
    return int(threshold)

def metric_more_or_less(metric, date_min, threshold):
    metric_on_date = metric_to_func_dict[metric](date_min)
    return "more" if metric_on_date > threshold else "less"

def get_threshold_and_metric_more_or_less():
    base_dict = get_random_dict()
    metric_vs_threshold = metric_more_or_less(base_dict["metric"], base_dict["date_min"], base_dict["threshold"])
    return {**base_dict, "metric_vs_threshold": metric_vs_threshold}

def fell_or_grew(metric, start_date, end_date):
    """Returns True if the metric grew or fell between the start and end date"""
    start_value = metric_to_func_dict[metric](start_date)
    end_value = metric_to_func_dict[metric](end_date)
    return "grew" if end_value > start_value else "fell"

def get_metric_fell_vs_grew():
    base_dict = get_random_dict()
    base_dict["date_max"] = str((pd.to_datetime(base_dict["date_min"]) + pd.Timedelta(days=random.randint(7, 30))).date())
    if base_dict["date_max"] > str(HARDCODED_CURRENT_TIME.date()):
        base_dict["date_max"] = str(HARDCODED_CURRENT_TIME.date())
    base_dict["natural_language_date_max"] = get_natural_language_date(base_dict["date_max"])
    fell_vs_grew = fell_or_grew(base_dict["metric"], base_dict["date_min"], base_dict["date_max"])
    return {**base_dict, "fell_vs_grew": fell_vs_grew}


def metric_plot_logic():
    base_dict = get_random_dict()
    answer = [get_plot_string(base_dict["metric"], base_dict["date_min"], base_dict["date_max"], base_dict["plot_type"])]
    return {**base_dict, "answer": answer}

def distribution_plot_on_day_logic():
    base_dict = get_random_dict()
    answer = [get_plot_string(base_dict["metric"], base_dict["date_min"], base_dict["date_min"], "histogram")]
    return {**base_dict, "answer": answer}


def metric_more_or_less_plot_logic():
    query_info = get_threshold_and_metric_more_or_less()
    if query_info["metric_vs_threshold"] == query_info["more_or_less"]:
        answer = [get_plot_string(query_info["metric"], query_info["date_min"], query_info["date_max"], "line")]
    else:
        answer = []
    return {"answer": answer, **query_info}

def metric_fell_or_grew_plot_logic():
    query_info = get_metric_fell_vs_grew()
    if query_info["fell_or_grew"] == query_info["fell_vs_grew"]:
        answer = [get_plot_string(query_info["metric"], query_info["date_min"], query_info["date_max"], "line")]
    else:
        answer = []
    return {"answer": answer, **query_info}

ANALYTICS_TEMPLATES = [
    {
        "query": """Can you make a {plot_type} chart of {natural_language_metric} since {natural_language_date}?""",
        "logic": metric_plot_logic,
    },
    {
        "query": """Plot the distribution of {natural_language_metric} on {natural_language_date}""",
        "logic": distribution_plot_on_day_logic,
    },
    {
        "query": """Can you chart the distribution of both {natural_language_metric} and {natural_language_metric_2} between {date_min} and {date_max}?""",
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} since {natural_language_date}, make a line plot of it since then""",
        "logic": metric_more_or_less_plot_logic,
    },
    {
        "query": """If {natural_language_metric} {fell_or_grew} from {natural_language_date} to {natural_language_date_max}, plot a line of that""",
        "logic": metric_fell_or_grew_plot_logic,
    },
    {
        "query": """Make a chart of the correlation between {natural_language_metric} and {natural_language_metric_2} with data from {date_min} to {date_max}""",
    },
    {
        "query": """If there's a {positive_or_negative} correlation between {natural_language_metric} and {natural_language_metric_2} since {date_min}, make a plot of it""",
    },
    {
        "query": """Can you plot the correlation between {natural_language_metric} and {natural_language_metric_2} since {date_min}?""",
    },
    {
        "query": """Make a bar chart comparing {natural_language_metric} and {natural_language_metric_2} since {date_min}""",
    },
    {
        "query": """Plot the {most_or_least} popular traffic source since {date_min}""", 
    },
]

max_queries_per_template = 1  # Limit the number of queries per template

if __name__ == "__main__":
    ANALYTICS_TEMPLATES = [t for t in ANALYTICS_TEMPLATES if "logic" in t]  # fix until we do logic for all templates
    generated_queries_and_answers = generate_all_queries_and_answers(ANALYTICS_TEMPLATES, max_queries_per_template)
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/analytics_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
