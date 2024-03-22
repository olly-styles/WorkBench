import pandas as pd
from langchain.tools import tool

ANALYTICS_DATA = pd.read_csv("data/processed/analytics_data.csv", dtype=str)
ANALYTICS_DATA["user_engaged"] = ANALYTICS_DATA["user_engaged"] == "True"  # Convert to boolean
PLOTS_DATA = pd.DataFrame(columns=["file_path"])
METRICS = ["total_visits", "session_duration_seconds", "user_engaged"]
METRIC_NAMES = ["total visits", "average session duration", "engaged users"]


def reset_state():
    """
    Resets the analytics data to the original state.
    """
    global ANALYTICS_DATA
    ANALYTICS_DATA = pd.read_csv("data/processed/analytics_data.csv", dtype=str)
    ANALYTICS_DATA["user_engaged"] = ANALYTICS_DATA["user_engaged"] == "True"  # Convert to boolean
    global PLOTS_DATA
    PLOTS_DATA = pd.DataFrame(columns=["file_path"])


@tool("analytics.get_visitor_information_by_id", return_direct=False)
def get_visitor_information_by_id(visitor_id=None):
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
    if not visitor_id:
        return "Visitor ID not provided."
    visitor_data = ANALYTICS_DATA[ANALYTICS_DATA["visitor_id"] == visitor_id].to_dict(orient="records")
    if visitor_data:
        return visitor_data
    else:
        return "Visitor not found."


@tool("analytics.create_plot", return_direct=False)
def create_plot(time_min=None, time_max=None, value_to_plot=None, plot_type=None):
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
    global PLOTS_DATA
    if not time_min:
        return "Start date not provided."
    if not time_max:
        return "End date not provided."
    if value_to_plot not in [
        "total_visits",
        "session_duration_seconds",
        "user_engaged",
        "visits_direct",
        "visits_referral",
        "visits_search_engine",
        "visits_social_media",
    ]:
        return "Value to plot must be one of 'total_visits', 'session_duration_seconds', 'user_engaged', 'direct', 'referral', 'search engine', 'social media'"
    if plot_type not in ["bar", "line", "scatter", "histogram"]:
        return "Plot type must be one of 'bar', 'line', 'scatter', or 'histogram'"

    # Plot the data here and save it to a file
    file_path = f"plots/{time_min}_{time_max}_{value_to_plot}_{plot_type}.png"
    PLOTS_DATA.loc[len(PLOTS_DATA)] = [file_path]
    return file_path


@tool("analytics.total_visits_count", return_direct=False)
def total_visits_count(time_min=None, time_max=None):
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
    if time_min:
        data = ANALYTICS_DATA[ANALYTICS_DATA["date_of_visit"] >= time_min]
    else:
        data = ANALYTICS_DATA
    if time_max:
        data = data[data["date_of_visit"] <= time_max]
    return data.groupby("date_of_visit").size().to_dict()


@tool("analytics.engaged_users_count", return_direct=False)
def engaged_users_count(time_min=None, time_max=None):
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
    if time_min:
        data = ANALYTICS_DATA[ANALYTICS_DATA["date_of_visit"] >= time_min]
    else:
        data = ANALYTICS_DATA[:]
    if time_max:
        data = data[data["date_of_visit"] <= time_max]
    data["user_engaged"] = data["user_engaged"].astype(bool).astype(int)

    return data.groupby("date_of_visit").sum()["user_engaged"].to_dict()


@tool("analytics.traffic_source_count", return_direct=False)
def traffic_source_count(time_min=None, time_max=None, traffic_source=None):
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
    if time_min:
        data = ANALYTICS_DATA[ANALYTICS_DATA["date_of_visit"] >= time_min]
    else:
        data = ANALYTICS_DATA[:]
    if time_max:
        data = data[data["date_of_visit"] <= time_max]

    if traffic_source:
        data["visits_from_source"] = (data["traffic_source"] == traffic_source).astype(int)
        return data.groupby("date_of_visit").sum()["visits_from_source"].to_dict()
    else:
        return data.groupby("date_of_visit").size().to_dict()


@tool("analytics.get_average_session_duration", return_direct=False)
def get_average_session_duration(time_min=None, time_max=None):
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
    if time_min:
        data = ANALYTICS_DATA[ANALYTICS_DATA["date_of_visit"] >= time_min]
    else:
        data = ANALYTICS_DATA
    if time_max:
        data = data[data["date_of_visit"] <= time_max]

    data["session_duration_seconds"] = data["session_duration_seconds"].astype(float)
    return (
        data[["date_of_visit", "session_duration_seconds"]]
        .groupby("date_of_visit")
        .mean()["session_duration_seconds"]
        .to_dict()
    )
