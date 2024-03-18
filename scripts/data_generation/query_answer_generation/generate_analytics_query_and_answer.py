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

traffic_sources = ANALYTICS_DATA["traffic_source"].unique()


def get_plot_string(metric, date_min, date_max, plot_type):
    return f"""analytics.create_plot.func(time_min="{date_min}", time_max="{date_max}", value_to_plot="{metric}", plot_type="{plot_type}")"""


def get_random_dict():
    date_min = random.choice(dates)
    metric = random.choice(METRICS)
    metric2 = random.choice([m for m in METRICS if m != metric])
    threshold = get_threshold(metric)
    growth_threshold = random.choice([0.05, 0.1, 0.15, 0.2, 0.25])
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
        "threshold": threshold,
        "growth_threshold": growth_threshold,
        "natural_language_growth_threshold": natural_language_growth_threshold,
    }


def get_threshold(metric):
    """Gets the threshold for a given metric over the whole time series"""
    func = metric_to_func_dict[metric]
    series = pd.Series(func(dates.min()))
    threshold_percentage = random.choice([0, 50, 100])
    threshold = np.percentile(series, threshold_percentage)
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
    base_dict["date_max"] = random.choice([d for d in dates if d > base_dict["date_min"]])
    natural_language_date_max = get_natural_language_date(base_dict["date_max"])
    answer = [
        get_plot_string(base_dict["metric"], base_dict["date_min"], base_dict["date_max"], "histogram"),
        get_plot_string(base_dict["metric2"], base_dict["date_min"], base_dict["date_max"], "histogram"),
    ]
    return {**base_dict, "answer": answer, "natural_language_date_max": natural_language_date_max}


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
    base_dict["more_or_less"] = random.choice(["more", "less"])
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


def metric_higher_or_lower(metric, date_min, date_max=None, threshold=0):
    metric_series = pd.Series(metric_to_func_dict[metric](date_min))
    previous_value = metric_series[date_min]
    current_value = metric_series.iloc[-1] if date_max is None else metric_series[date_max]
    pct_change = (current_value - previous_value) / previous_value
    if pct_change < 0 and abs(pct_change) > threshold:
        return "lower"
    elif pct_change > 0 and pct_change > threshold:
        return "higher"
    else:
        return "not changed"


def get_threshold_and_higher_or_lower(date_min=None, date_max=None):
    base_dict = get_random_dict()
    base_dict["higher_or_lower"] = random.choice(["higher", "lower"])
    date_min = base_dict["date_min"] if date_min is None else date_min
    date_max = base_dict["date_max"] if date_max is None else date_max
    higher_or_lower = metric_higher_or_lower(base_dict["metric"], date_min, date_max, base_dict["growth_threshold"])
    return {**base_dict, "growth_vs_threshold": higher_or_lower}


def metric_higher_or_lower_plot_logic(date_min=None, date_max=None):
    query_info = get_threshold_and_higher_or_lower(date_min, date_max)
    query_info["date_min"] = date_min if date_min is not None else query_info["date_min"]
    query_info["date_max"] = date_max if date_max is not None else query_info["date_max"]
    if query_info["higher_or_lower"] == query_info["growth_vs_threshold"]:
        answer = [get_plot_string(query_info["metric"], query_info["date_min"], query_info["date_max"], "line")]
    else:
        answer = []
    return {"answer": answer, **query_info}


def metric_higher_or_lower_day_of_week_plot_logic():
    day_in_last_week = random.choice([1, 2, 3, 4, 5, 6])
    date_min = str(HARDCODED_CURRENT_TIME.date() - pd.Timedelta(day_in_last_week, "D"))
    day_of_week = pd.to_datetime(date_min).day_name()
    query_info = metric_higher_or_lower_plot_logic(date_min)
    return {**query_info, "day_of_week": day_of_week}


def metric_higher_or_lower_past_weeks_plot_logic():
    day_in_last_week = random.choice([1, 2, 3, 4, 5, 6])
    date_last_week = str(HARDCODED_CURRENT_TIME.date() - pd.Timedelta(day_in_last_week, "D"))
    date_week_before_last = str(HARDCODED_CURRENT_TIME.date() - pd.Timedelta(day_in_last_week + 7, "D"))
    day_of_week = pd.to_datetime(date_last_week).day_name().lower()

    query_info = metric_higher_or_lower_plot_logic(date_week_before_last, date_last_week)
    return {**query_info, "day_of_week": day_of_week}


def get_relative_growth(metric1, metric2, date_min):
    metric1_series = pd.Series(metric_to_func_dict[metric1](date_min))
    metric1_growth = (metric1_series.iloc[-1] - metric1_series[date_min]) / metric1_series[date_min]

    metric2_series = pd.Series(metric_to_func_dict[metric2](date_min))
    metric2_growth = (metric2_series.iloc[-1] - metric2_series[date_min]) / metric2_series[date_min]

    return metric1_growth, metric2_growth


def relative_growth_two_plots_logic():
    base_dict = get_random_dict()
    day_in_last_week = random.choice([1, 2, 3, 4, 5, 6])
    date_min = str(HARDCODED_CURRENT_TIME.date() - pd.Timedelta(day_in_last_week, "D"))
    day_of_week = pd.to_datetime(date_min).day_name()

    metric1_growth, metric2_growth = get_relative_growth(base_dict["metric"], base_dict["metric2"], date_min)

    if metric1_growth > metric2_growth:
        answer = [
            get_plot_string(base_dict["metric"], date_min, base_dict["date_max"], "line"),
            get_plot_string(base_dict["metric2"], date_min, base_dict["date_max"], "line"),
        ]
    else:
        answer = []
    return {**base_dict, "answer": answer, "day_of_week": day_of_week}


def metric_two_plots_logic():
    base_dict = get_random_dict()
    answer = [
        get_plot_string(base_dict["metric"], base_dict["date_min"], base_dict["date_max"], "bar"),
        get_plot_string(base_dict["metric2"], base_dict["date_min"], base_dict["date_max"], "bar"),
    ]
    return {**base_dict, "answer": answer}


def plot_most_popular_traffic_source_logic():
    base_dict = get_random_dict()
    traffic_source_popularity = {
        s: pd.Series(analytics.traffic_source_count.func(base_dict["date_min"], traffic_source=s)).mean()
        for s in traffic_sources
    }
    growth = -10000
    for pop in traffic_source_popularity:
        if traffic_source_popularity[pop] > growth:
            growth = traffic_source_popularity[pop]
            most_popular = pop

    answer = [get_plot_string(most_popular, base_dict["date_min"], base_dict["date_max"], "line")]
    return {**base_dict, "most_or_least": "most", "answer": answer}


def plot_relative_traffic_source_logic():
    base_dict = get_random_dict()
    traffic_source_1 = random.choice(traffic_sources)
    traffic_source_2 = random.choice([s for s in traffic_sources if s != traffic_source_1])

    n_weeks = random.choice([2, 3, 4, 5, 6])
    date_min = str(HARDCODED_CURRENT_TIME.date() - pd.Timedelta(n_weeks, "W"))
    base_dict["date_min"] = date_min
    traffic_source_1_popularity = pd.Series(
        analytics.traffic_source_count.func(date_min, traffic_source=traffic_source_1)
    ).mean()
    traffic_source_2_popularity = pd.Series(
        analytics.traffic_source_count.func(date_min, traffic_source=traffic_source_2)
    ).mean()

    if traffic_source_1_popularity > traffic_source_2_popularity:
        answer = [
            get_plot_string(traffic_source_1, base_dict["date_min"], base_dict["date_max"], "bar"),
            get_plot_string(traffic_source_2, base_dict["date_min"], base_dict["date_max"], "bar"),
        ]

    else:
        answer = []
    return {
        **base_dict,
        "traffic_source_1": traffic_source_1,
        "traffic_source_2": traffic_source_2,
        "answer": answer,
        "n_weeks": n_weeks,
    }


ANALYTICS_TEMPLATES = [
    {
        "query": """Can you make a {plot_type} chart of {natural_language_metric} since {natural_language_date}?""",
        "alternative_queries": [
            """Plot {natural_language_metric} since {natural_language_date} as a {plot_type} chart""",
            """Create a {plot_type} chart of {natural_language_metric} since {natural_language_date}""",
        ],
        "logic": metric_plot_logic,
    },
    {
        "query": """Plot the distribution of {natural_language_metric} on {natural_language_date}""",
        "alternative_queries": [
            """Can you make a histogram of {natural_language_metric} on {natural_language_date}?""",
            """please plot the distribution of the {natural_language_metric} metric on {natural_language_date}""",
        ],
        "logic": distribution_plot_on_day_logic,
    },
    {
        "query": """Can you plot the distribution of both {natural_language_metric} and {natural_language_metric_2} between {natural_language_date} and {natural_language_date_max}??""",
        "alternative_queries": [
            """I need a histogram of {natural_language_metric} and {natural_language_metric_2} between {natural_language_date} and {natural_language_date_max}""",
            """Show me the distribution of {natural_language_metric} and {natural_language_metric_2} between {natural_language_date} and {natural_language_date_max}""",
        ],
        "logic": distribution_plot_on_day_two_metrics_logic,
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}, make a line plot of it since then""",
        "alternative_queries": [
            """was {natural_language_metric} {more_or_less} than {threshold} at any time since {natural_language_date}? If so, please plot it as a line chart""",
            """Can you make a line chart of {natural_language_metric} since {natural_language_date} if it was {more_or_less} than {threshold} since at any time {natural_language_date}?""",
        ],
        "logic": metric_more_or_less_plot_logic,
    },
    {
        "query": """Make bar charts showing {natural_language_metric} and {natural_language_metric_2} since {date_min}""",
        "alternative_queries": [
            """can you show me bar charts of {natural_language_metric} and {natural_language_metric_2} since {date_min}?""",
            """I need bar charts of {natural_language_metric} and {natural_language_metric_2} since {date_min}""",
        ],
        "logic": metric_two_plots_logic,
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} any time in the last {past_n_weeks} weeks, make a line plot of it since then""",
        "alternative_queries": [
            """Was {natural_language_metric} {more_or_less} than {threshold} at any time in the last {past_n_weeks} weeks? If so, please plot it as a line chart""",
            """Can you make a line chart of {natural_language_metric} since the last {past_n_weeks} weeks if it was {more_or_less} than {threshold} at any time in the last {past_n_weeks} weeks?""",
        ],
        "logic": metric_more_or_less_past_weeks_plot_logic,
    },
    {
        "query": """If {natural_language_metric} yesterday is more than {natural_language_growth_threshold} {higher_or_lower} than {natural_language_date}, make a line plot of it since then""",
        "alternative_queries": [
            """Was {natural_language_metric} yesterday more than {natural_language_growth_threshold} {higher_or_lower} than {natural_language_date}? If so, please plot it as a line chart""",
            """Can you make a line chart of {natural_language_metric} since {natural_language_date} if it was more than {natural_language_growth_threshold} {higher_or_lower} than {natural_language_date} yesterday?""",
        ],
        "logic": metric_higher_or_lower_plot_logic,
    },
    {
        "query": """If {natural_language_metric} yesterday is more than {natural_language_growth_threshold} {higher_or_lower} than it was on {day_of_week}, make a line plot of it since then""",
        "alternative_queries": [
            """Was {natural_language_metric} yesterday more than {natural_language_growth_threshold} {higher_or_lower} than it was on {day_of_week}? If so, please plot it as a line chart""",
            """Can you make a line chart of {natural_language_metric} since {day_of_week} if it was more than {natural_language_growth_threshold} {higher_or_lower} than it was yesterday?""",
        ],
        "logic": metric_higher_or_lower_day_of_week_plot_logic,
    },
    {
        "query": """If {natural_language_metric} on {day_of_week} was more than {natural_language_growth_threshold} {higher_or_lower} than it was the previous {day_of_week}, make a line plot of it over that period.""",
        "alternative_queries": [
            """Was {natural_language_metric} on {day_of_week} more than {natural_language_growth_threshold} {higher_or_lower} than it was the previous {day_of_week}? If so, please plot it as a line chart""",
            """make a line chart of {natural_language_metric} over the period from {day_of_week} to the previous {day_of_week} if it was more than {natural_language_growth_threshold} {higher_or_lower} on {day_of_week} than it was the previous {day_of_week}""",
        ],
        "logic": metric_higher_or_lower_past_weeks_plot_logic,
    },
    {
        "query": """Can you check the percent growth of {natural_language_metric} since {day_of_week}? If it grew by more than {natural_language_metric_2}, plot both lines since then""",
        "alternative_queries": [
            """Check the percent growth of {natural_language_metric} since {day_of_week}. If it grew by more than {natural_language_metric_2}, plot both lines since then""",
            """if {natural_language_metric} grew by more than {natural_language_metric_2} since {day_of_week}, make a line plot of both since then""",
        ],
        "logic": relative_growth_two_plots_logic,
    },
    {
        "query": """Can you make a line plot of the {most_or_least} popular traffic source since {natural_language_date}?""",
        "alternative_queries": [
            """Make a line plot of the {most_or_least} popular traffic source since {natural_language_date}""",
            """plot the {most_or_least} popular traffic source since {natural_language_date}""",
        ],
        "logic": plot_most_popular_traffic_source_logic,
    },
    {
        "query": """If we got more traffic from {traffic_source_1} than {traffic_source_2} during the last {n_weeks} weeks, make bar charts of both over that period""",
        "alternative_queries": [
            """Make bar charts of {traffic_source_1} and {traffic_source_2} over the last {n_weeks} weeks if we got more traffic from {traffic_source_1} than {traffic_source_2}""",
            """did we get more traffic from {traffic_source_1} than {traffic_source_2} during the last {n_weeks} weeks? If so, make bar charts of both over that period""",
        ],
        "logic": plot_relative_traffic_source_logic,
    },
]
for d in ANALYTICS_TEMPLATES:
    d["domains"] = ["analytics"]

max_queries_per_template = 10  # Limit the number of queries per template

if __name__ == "__main__":
    generated_queries_and_answers = generate_all_queries_and_answers(ANALYTICS_TEMPLATES, max_queries_per_template)
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/analytics_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
