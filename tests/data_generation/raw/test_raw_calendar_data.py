import pandas as pd

event_names = pd.read_csv("data/raw/events.csv", header=None)
emails = pd.read_csv("data/raw/emails.csv", header=None)


def test_event_names_unique():
    assert len(event_names) == len(event_names.drop_duplicates())


def test_emails_unique():
    assert len(emails) == len(emails.drop_duplicates())
