import pandas as pd

from src.tools.calender import get_event_information_by_id


calender_events = pd.read_csv("data/processed/calender_events.csv")


def test_get_event_information_by_id():
    """
    Tests get_event_information_by_id.
    """
    args = {"id": "0395", "field": "event_name"}
    assert get_event_information_by_id(args) == {
        "event_name": "Digital Transformation Summit"
    }


def test_get_event_information_by_id_no_id():
    """
    Tests get_event_information_by_id with no ID.
    """
    args = {}
    event = get_event_information_by_id(args)
    assert event == "No ID provided."


def test_get_event_information_by_id_no_field():
    """
    Tests get_event_information_by_id with no field.
    """
    args = {"id": "0395"}
    event = get_event_information_by_id(args)
    assert event == "No field provided."


def test_get_event_information_by_id_field_not_found():
    """
    Tests get_event_information_by_id with field not found.
    """
    args = {"id": "0395", "field": "field_does_not_exist"}
    event = get_event_information_by_id(args)
    assert event == "Field not found."
