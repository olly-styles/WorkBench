import pandas as pd

email_data = pd.read_csv("data/processed/emails.csv").sort_values("sent_datetime")
email_data["send_date"] = pd.to_datetime(email_data["sent_datetime"]).dt.date


def test_no_two_emails_same_subject_same_day():
    """
    Tests that no two emails with the same subject are on the same day.
    """
    grouped = email_data.groupby(["send_date", "subject"]).size()
    assert len(grouped[grouped > 1]) == 0


def test_no_two_emails_same_sender_same_time():
    """
    Tests that no two emails are sent by the same person at the same time.
    """
    grouped = email_data.groupby(["sent_datetime", "sender"]).size()
    assert len(grouped[grouped > 1]) == 0


def test_no_two_emails_same_subject_same_time():
    """
    Tests that no two emails have the same subject at the same time.
    """
    grouped = email_data.groupby(["sent_datetime", "subject"]).size()
    assert len(grouped[grouped > 1]) == 0
