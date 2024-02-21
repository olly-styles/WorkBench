import pandas as pd
import pytest

from src.tools import analytics

# Sample analytics data for testing
test_analytics_data = [
    {
        "date_of_visit": "2023-10-01",
        "visitor_id": "000",
        "page_views": "3",
        "session_duration": "10.0",
        "traffic_source": "search engine",
        "user_engaged": False,
    },
    {
        "date_of_visit": "2023-10-02",
        "visitor_id": "001",
        "page_views": "5",
        "session_duration": "15.0",
        "traffic_source": "direct",
        "user_engaged": True,
    },
]
analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)


def test_get_visitor_information_by_id():
    """
    Tests get_visitor_information_by_id when visitor ID is found.
    """
    analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)
    expected_result = {
        "date_of_visit": "2023-10-01",
        "visitor_id": "000",
        "page_views": "3",
        "session_duration": "10.0",
        "traffic_source": "search engine",
        "user_engaged": False,
    }
    assert analytics.get_visitor_information_by_id.func("000") == [expected_result]


def test_get_visitor_information_by_id_not_found():
    """
    Tests get_visitor_information_by_id when visitor ID is not found.
    """
    analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)
    assert analytics.get_visitor_information_by_id.func("999") == "Visitor not found."


def test_get_visitor_information_by_id_no_id_provided():
    """
    Tests get_visitor_information_by_id with no visitor ID provided.
    """
    analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)
    assert analytics.get_visitor_information_by_id.func() == "Visitor ID not provided."


def test_create_plot():
    """
    Tests create_plot.
    """
    analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)
    value_to_plot = "page_views"
    time_min = "2023-10-01"
    time_max = "2023-10-02"
    plot_type = "bar"
    expected_file_path = f"plots/{time_min}_{time_max}_{value_to_plot}_{plot_type}.png"
    assert analytics.create_plot.func(time_min, time_max, value_to_plot, plot_type) == expected_file_path


def test_create_plot_missing_arguments():
    """
    Tests create_plot with missing arguments.
    """
    analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)
    assert analytics.create_plot.func() == "Start date not provided."
    assert analytics.create_plot.func("2023-10-01") == "End date not provided."
    assert (
        analytics.create_plot.func("2023-10-01", "2023-10-02")
        == "Value to plot must be one of 'page_views', 'session_duration_seconds', 'traffic_source', 'user_engaged'"
    )
    assert (
        analytics.create_plot.func("2023-10-01", "2023-10-02", "page_views")
        == "Plot type must be one of 'bar', 'line', 'scatter', or 'histogram'"
    )


def test_total_visits_count():
    """
    Tests the total_visits_count function.
    """
    analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)
    # Test with a specific date range
    assert analytics.total_visits_count.func("2023-10-01", "2023-10-02") == 2
    # Test with a broader date range
    assert analytics.total_visits_count.func("2023-09-30", "2023-10-03") == 2
    # Test with no date range (should count all visits)
    assert analytics.total_visits_count.func() == len(test_analytics_data)
    # Test with a date range that includes no visits
    assert analytics.total_visits_count.func("2023-10-03", "2023-10-04") == 0


def test_engaged_users_count():
    """
    Tests the engaged_users_count function.
    """
    analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)
    # Test with a specific date range
    assert analytics.engaged_users_count.func("2023-10-01", "2023-10-02") == 1
    # Test with a broader date range
    assert analytics.engaged_users_count.func("2023-09-30", "2023-10-03") == 1
    # Test with no date range (should count all engaged users)
    assert analytics.engaged_users_count.func() == 1
    # Test with a date range that includes no engaged users
    assert analytics.engaged_users_count.func("2023-10-03", "2023-10-04") == 0


def test_traffic_source_count():
    """
    Tests the traffic_source_count function.
    """
    analytics.ANALYTICS_DATA = pd.DataFrame(test_analytics_data)
    # Test with a specific date range
    assert analytics.traffic_source_count.func("2023-10-01", "2023-10-02", "search engine") == 1
    # Test with a broader date range
    assert analytics.traffic_source_count.func("2023-09-30", "2023-10-03", "search engine") == 1
    # Test with no date range (should count all visits)
    assert analytics.traffic_source_count.func() == 2
    # Test with a date range that includes no visits
    assert analytics.traffic_source_count.func("2023-10-03", "2023-10-04", "search engine") == 0
