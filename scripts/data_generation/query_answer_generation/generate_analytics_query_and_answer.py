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
    "total_visits": analytics.total_visits_count,
    "session_duration_seconds": analytics.get_average_session_duration,
    "traffic_source": analytics.traffic_source_count,
    "user_engaged": analytics.engaged_users_count,
}


def get_plot_string(metric, date_min, date_max, plot_type):
    return f"""analytics.create_plot.func(time_min="{date_min}", time_max="{date_max}", value_to_plot="{metric}", plot_type="{plot_type}")"""


def get_random_dict():
    date_min = random.choice(dates)
    metric = random.choice(METRICS)
    metric2 = random.choice([m for m in METRICS if m != metric])
    threshold = get_threshold(metric)
    growth_threshold = random.choice([0.1, 0.2, 0.3, 0.4, 0.5])
    natural_language_growth_threshold = f"{int(100*growth_threshold)}%"
    return {
        "date_min": date_min,
        "date_max": str(ANALYTICS_DATA["date_of_visit"].max()),
        "metric": metric,
        "metric2": metric2,
        "natural_language_date": get_natural_language_date(date_min),
        "natural_language_metric": metric_naming_dict[metric],
        "natural_language_metric_2": metric_naming_dict[metric2],
        "plot_type": random.choice(["line", "bar", "scatter", "histogram"]),
        "more_or_less": random.choice(["more", "less"]),
        "fallen_or_grown": random.choice(["fallen", "grown"]),
        "threshold": threshold,
        "growth_threshold": growth_threshold,
        "natural_language_growth_threshold": natural_language_growth_threshold,
    }


def get_threshold(metric):
    """Gets the threshold for a given metric over the whole time series"""
    metric_name = "page_views" if metric == "total_visits" else metric
    data = ANALYTICS_DATA[["date_of_visit", metric_name]]
    data.loc[:, metric_name] = data[metric_name].astype(float)
    threshold_percentage = random.choice([0, 50, 100])
    threshold = np.percentile(data.groupby("date_of_visit").mean(), threshold_percentage)
    return int(threshold)


def metric_more_or_less(metric, date_min, threshold):
    metric_series = metric_to_func_dict[metric](date_min)
    metric_on_date = metric_series[date_min]
    return "more" if metric_on_date > threshold else "less"

def metric_plot_logic():
    base_dict = get_random_dict()
    answer = [
        get_plot_string(base_dict["metric"], base_dict["date_min"], base_dict["date_max"], base_dict["plot_type"])
    ]
    return {**base_dict, "answer": answer}

def distribution_plot_on_day_logic():
    base_dict = get_random_dict()
    answer = [get_plot_string(base_dict["metric"], base_dict["date_min"], base_dict["date_min"], "histogram")]
    return {**base_dict, "answer": answer}


def distribution_plot_on_day_two_metrics_logic():
    base_dict = get_random_dict()
    answer = [
        get_plot_string(base_dict["metric"], base_dict["date_min"], base_dict["date_max"], "histogram"),
        get_plot_string(base_dict["metric2"], base_dict["date_min"], base_dict["date_max"], "histogram"),
    ]
    return {**base_dict, "answer": answer}


def metric_more_or_less_any_time(metric, date_min, threshold):
    series_func = metric_to_func_dict[metric]
    metric_series = pd.Series(series_func(date_min))
    if (metric_series > threshold).sum() == 0:
        return "less"
    elif (metric_series < threshold).sum() == 0:
        return "more"
    else:
        return "both more and less"

def get_threshold_and_metric_more_or_less(date_min=None):
    base_dict = get_random_dict()
    date_min = base_dict["date_min"] if date_min is None else date_min
    metric_vs_threshold = metric_more_or_less_any_time(base_dict["metric"], date_min, base_dict["threshold"])
    return {**base_dict, "metric_vs_threshold": metric_vs_threshold}

def metric_more_or_less_plot_logic(date_min=None):
    query_info = get_threshold_and_metric_more_or_less(date_min)
    query_info["date_min"] = date_min if date_min is not None else query_info["date_min"]
    if query_info["more_or_less"] in query_info["metric_vs_threshold"]:
        answer = [get_plot_string(query_info["metric"], query_info["date_min"], query_info["date_max"], "line")]
    else:
        answer = []
    return {"answer": answer, **query_info}

def metric_more_or_less_past_weeks_plot_logic():
    n_weeks = random.choice([1, 2, 3, 4, 5, 6])
    date_min = str(HARDCODED_CURRENT_TIME.date() - pd.Timedelta(n_weeks, "W"))
    return {**metric_more_or_less_plot_logic(date_min), "past_n_weeks": n_weeks}

def metric_fallen_or_grown(metric, date_min, threshold=0):
    metric_series = pd.Series(metric_to_func_dict[metric](date_min))
    previous_value = metric_series[date_min]
    current_value = metric_series.iloc[-1]
    pct_change = (current_value - previous_value) / previous_value
    if pct_change < 0 and abs(pct_change) > threshold:
        return "fallen"
    elif pct_change > 0 and pct_change > threshold:
        return "grown"
    else:
        return "not changed"

def get_threshold_and_fallen_or_grown(date_min=None):
    base_dict = get_random_dict()
    date_min = base_dict["date_min"] if date_min is None else date_min
    fallen_or_grown = metric_fallen_or_grown(base_dict["metric"], date_min, base_dict["growth_threshold"])
    return {**base_dict, "growth_vs_threshold": fallen_or_grown}

def metric_fallen_or_grown_plot_logic(date_min=None):
    query_info = get_threshold_and_fallen_or_grown(date_min)
    query_info["date_min"] = date_min if date_min is not None else query_info["date_min"]
    if query_info["fallen_or_grown"] == query_info["growth_vs_threshold"]:
        answer = [get_plot_string(query_info["metric"], query_info["date_min"], query_info["date_max"], "line")]
    else:
        answer = []
    return {"answer": answer, **query_info}

def metric_fallen_or_grown_past_weeks_plot_logic():
    n_weeks = random.choice([1, 2, 3, 4, 5, 6])
    date_min = str(HARDCODED_CURRENT_TIME.date() - pd.Timedelta(n_weeks, "W"))
    return {**metric_fallen_or_grown_plot_logic(date_min), "past_n_weeks": n_weeks}

def metric_two_plots_logic():
    base_dict = get_random_dict()
    answer = [
        get_plot_string(base_dict["metric"], base_dict["date_min"], base_dict["date_max"], "bar"),
        get_plot_string(base_dict["metric2"], base_dict["date_min"], base_dict["date_max"], "bar"),
    ]
    return {**base_dict, "answer": answer}


ANALYTICS_TEMPLATES = [
    {
        "query": """Can you make a {plot_type} chart of {natural_language_metric} since {natural_language_date}?""",
        "logic": metric_plot_logic,
    },
    {
        "query": """Can you plot the distribution of both {natural_language_metric} and {natural_language_metric_2} between {date_min} and {date_max}?""",
        "logic": distribution_plot_on_day_two_metrics_logic,
    },
    
    {
        "query": """Make bar charts showing {natural_language_metric} and {natural_language_metric_2} since {date_min}""",
        "logic": metric_two_plots_logic,
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}, make a line plot of it since then""",
        "logic": metric_more_or_less_plot_logic,
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} any time in the last {past_n_weeks} weeks, make a line plot of it since then""",
        "logic": metric_more_or_less_past_weeks_plot_logic,
    },
    {
        "query": """If {natural_language_metric} has {fallen_or_grown} by more than {natural_language_growth_threshold} since {natural_language_date}, make a line plot of it since then""",
        "logic": metric_fallen_or_grown_plot_logic,
    },
    {
        "query": """If {natural_language_metric} has {fallen_or_grown} by more than {natural_language_growth_threshold} in the last {past_n_weeks} weeks, make a line plot over that period""",
        "logic": metric_fallen_or_grown_past_weeks_plot_logic,
    },
]
for d in ANALYTICS_TEMPLATES:
    d["domains"] = ["analytics"] 

max_queries_per_template = 3  # Limit the number of queries per template

if __name__ == "__main__":
    generated_queries_and_answers = generate_all_queries_and_answers(ANALYTICS_TEMPLATES[3:], max_queries_per_template)
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/analytics_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
