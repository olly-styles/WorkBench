import pandas as pd

email_data = pd.read_csv("data/processed/emails.csv").sort_values("sent_date")


# No two emails on the same day with the same subject
def test_no_two_emails_same_subject_same_day():
    """
    Tests that no two emails with the same subject are on the same day.
    """
    grouped = email_data.groupby(["sent_date", "subject"]).size()
    assert len(grouped[grouped > 1]) == 0
