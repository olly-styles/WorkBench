import json

import pandas as pd

from src.tools._utils import filter_by_date_range
from src.tools.state import get_state
from src.tools.tool import tool

VALID_VALUES_TO_PLOT = [
    "total_visits",
    "session_duration_seconds",
    "user_engaged",
    "visits_direct",
    "visits_referral",
    "visits_search_engine",
    "visits_social_media",
]
VALID_PLOT_TYPES = ["bar", "line", "scatter", "histogram"]

METRICS = ["total_visits", "session_duration_seconds", "user_engaged"]
METRIC_NAMES = ["total visits", "average session duration", "engaged users"]


@tool("analytics.get_visitor_information_by_id")
def get_visitor_information_by_id(visitor_id: str | None = None) -> str:
    """
    Returns the analytics data for a given visitor ID.

    Parameters
    ----------
    visitor_id : str, optional
        ID of the visitor.

    Returns
    -------
    visitor_data : dict
        Analytics data for the given visitor ID.

    Examples
    --------
    >>> analytics.get_visitor_information_by_id("000")
    {{"date_of_visit": "2023-10-01", "visitor_id": "000", "page_views": "3", "session_duration_seconds": "10.0", "traffic_source": "search engine", "user_engaged": "False"}}

    """
    state = get_state()
    if not visitor_id:
        return "Visitor ID not provided."
    visitor_data = state.analytics_data[state.analytics_data["visitor_id"] == visitor_id].to_dict(orient="records")
    return json.dumps(visitor_data) if visitor_data else "Visitor not found."


@tool("analytics.create_plot")
def create_plot(
    time_min: str | None = None,
    time_max: str | None = None,
    value_to_plot: str | None = None,
    plot_type: str | None = None,
) -> str:
    """
    Plots the analytics data for a given time range and value.

    Parameters
    ----------
    time_min : str, optional
        Start date of the time range. Date format is "YYYY-MM-DD".
    time_max : str, optional
        End date of the time range. Date format is "YYYY-MM-DD".
    value_to_plot : str, optional
        Value to plot. Available values are: "total_visits", "session_duration_seconds", "user_engaged", "visits_direct", "visits_referral", "visits_search_engine", "visits_social_media"
    plot_type : str, optional
        Type of plot. Can be "bar", "line", "scatter" or "histogram"

    Returns
    -------
    file_path : str
        Path to the plot file. Filename is {{time_min}}_{{time_max}}_{{value_to_plot}}_{{plot_type}}.png.

    Examples
    --------
    >>> analytics.create_plot("2023-10-01", "2023-12-31", "total_visits")
    "plots/2023-10-01_2023-12-31_total_visits.png"

    """
    state = get_state()
    if not time_min:
        return "Start date not provided."
    if not time_max:
        return "End date not provided."
    if value_to_plot not in VALID_VALUES_TO_PLOT:
        return f"Value to plot must be one of {', '.join(repr(v) for v in VALID_VALUES_TO_PLOT)}"
    if plot_type not in VALID_PLOT_TYPES:
        return f"Plot type must be one of {', '.join(repr(v) for v in VALID_PLOT_TYPES)}"

    # Plot the data here and save it to a file
    file_path = f"plots/{time_min}_{time_max}_{value_to_plot}_{plot_type}.png"
    new_row = pd.DataFrame({"file_path": [file_path]})
    state.plots_data = pd.concat([state.plots_data, new_row], ignore_index=True)
    return file_path


@tool("analytics.total_visits_count")
def total_visits_count(time_min: str | None = None, time_max: str | None = None) -> str:
    """
    Returns the total number of visits within a specified time range.

    Parameters
    ----------
    time_min : str, optional
        Start date of the time range. Date format is "YYYY-MM-DD".
    time_max : str, optional
        End date of the time range. Date format is "YYYY-MM-DD".

    Returns
    -------
    total_visits : dict
        Total number of visits in the specified time range.

    Examples
    --------
    >>> analytics.total_visits_count("2023-10-01", "2023-10-06")
    {{"2023-10-01": 1, "2023-10-02": 2, "2023-10-03": 3, "2023-10-04": 1, "2023-10-05": 0, "2023-10-06": 4}}
    """
    data = filter_by_date_range(get_state().analytics_data, "date_of_visit", time_min, time_max)
    return json.dumps(data.groupby("date_of_visit").size().to_dict())


@tool("analytics.engaged_users_count")
def engaged_users_count(time_min: str | None = None, time_max: str | None = None) -> str:
    """
    Returns the number of engaged users within a specified time range.

    Parameters
    ----------
    time_min : str, optional
        Start date of the time range. Date format is "YYYY-MM-DD".
    time_max : str, optional
        End date of the time range. Date format is "YYYY-MM-DD".

    Returns
    -------
    engaged_users : dict
        Number of engaged users in the specified time range.

    Examples
    --------
    >>> analytics.engaged_users_count("2023-10-01", "2023-10-06")
    {{"2023-10-01": 1, "2023-10-02": 2, "2023-10-03": 2, "2023-10-04": 1, "2023-10-05": 0, "2023-10-06": 4}}
    """
    data = filter_by_date_range(get_state().analytics_data, "date_of_visit", time_min, time_max)
    data["user_engaged"] = data["user_engaged"].astype(bool).astype(int)

    return json.dumps(data.groupby("date_of_visit")["user_engaged"].sum().to_dict())


@tool("analytics.traffic_source_count")
def traffic_source_count(
    time_min: str | None = None, time_max: str | None = None, traffic_source: str | None = None
) -> str:
    """
    Returns the number of visits from a specific traffic source within a specified time range.

    Parameters
    ----------
    time_min : str, optional
        Start date of the time range. Date format is "YYYY-MM-DD".
    time_max : str, optional
        End date of the time range. Date format is "YYYY-MM-DD".
    traffic_source : str, optional
        Traffic source to filter the visits. Available values are: "direct", "referral", "search engine", "social media"

    Returns
    -------
    traffic_source_visits : dict
        Number of visits from the specified traffic source in the specified time range.

    Examples
    --------
    >>> analytics.traffic_source_count("2023-10-01", "2023-10-06", "search engine")
    {{"2023-10-01": 0, "2023-10-02": 1, "2023-10-03": 0, "2023-10-04": 3, "2023-10-05": 2, "2023-10-06": 4}}
    """
    data = filter_by_date_range(get_state().analytics_data, "date_of_visit", time_min, time_max)

    if traffic_source:
        data["visits_from_source"] = (data["traffic_source"] == traffic_source).astype(int)
        return json.dumps(data.groupby("date_of_visit")["visits_from_source"].sum().to_dict())
    return json.dumps(data.groupby("date_of_visit").size().to_dict())


@tool("analytics.get_average_session_duration")
def get_average_session_duration(time_min: str | None = None, time_max: str | None = None) -> str:
    """
    Returns the average session duration within a specified time range.

    Parameters
    ----------
    time_min : str, optional
        Start date of the time range. Date format is "YYYY-MM-DD".
    time_max : str, optional
        End date of the time range. Date format is "YYYY-MM-DD".

    Returns
    -------
    average_session_duration : float
        Average session duration in seconds in the specified time range.

    Examples
    --------
    >>> analytics.get_average_session_duration("2023-10-01", "2023-10-06")
    {{"2023-10-01": 10.0, "2023-10-02": 20.5, "2023-10-03": 32.8, "2023-10-04": 40.2, "2023-10-05": 5.3, "2023-10-06": 53.0}}
    """
    data = filter_by_date_range(get_state().analytics_data, "date_of_visit", time_min, time_max)

    data["session_duration_seconds"] = data["session_duration_seconds"].astype(float)
    return json.dumps(data.groupby("date_of_visit")["session_duration_seconds"].mean().to_dict())
