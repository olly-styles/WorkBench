import json
from collections.abc import Mapping, Sequence

import pandas as pd

from src.tools import email
from src.tools.state import get_state

# Sample data for emails
test_emails = [
    {
        "email_id": "12345678",
        "inbox/outbox": "inbox",
        "sender/recipient": "jane@example.com",
        "subject": "Project Update",
        "sent_datetime": "2024-01-10 09:30:00",
        "body": "Please find the project update attached.",
    },
    {
        "email_id": "12345679",
        "inbox/outbox": "inbox",
        "sender/recipient": "mark@example.com",
        "subject": "Meeting Request",
        "sent_datetime": "2024-01-11 10:15:00",
        "body": "Can we schedule a meeting for next week?",
    },
]


def _set_emails(emails: Sequence[Mapping[str, str]]):
    get_state().emails = pd.DataFrame(emails)


def test_get_email_information_by_id():
    """
    Tests get_email_information_by_id.
    """
    _set_emails(test_emails)
    assert email.get_email_information_by_id("12345678", "subject") == json.dumps({"subject": "Project Update"})


def test_get_email_information_missing_arguments():
    """
    Tests get_email_information_by_id with no ID and no field.
    """
    _set_emails(test_emails)
    assert email.get_email_information_by_id() == "Email ID not provided."
    assert email.get_email_information_by_id("12345678") == "Field not provided."


def test_get_email_information_by_id_field_not_found():
    """
    Tests get_email_information_by_id with field not found.
    """
    _set_emails(test_emails)
    result = email.get_email_information_by_id("12345678", "field_does_not_exist")
    assert result == "Field not found."


def test_search_emails():
    """
    Tests search_emails.
    """
    _set_emails(test_emails)
    assert json.loads(email.search_emails("Meeting Request"))[0] == {
        "email_id": "12345679",
        "inbox/outbox": "inbox",
        "sender/recipient": "mark@example.com",
        "subject": "Meeting Request",
        "sent_datetime": "2024-01-11 10:15:00",
        "body": "Can we schedule a meeting for next week?",
    }


def test_search_emails_none_found():
    """
    Tests search_emails with no emails found.
    """
    _set_emails(test_emails)
    assert json.loads(email.search_emails("email_does_not_exist")) == []


def test_search_emails_multiple_fields_at_once():
    """
    Tests search_emails with multiple fields at once, for example, searching for both a name and an email subject at the same time.
    """
    _set_emails(test_emails)
    assert json.loads(email.search_emails("Mark Meeting Request"))[0] == {
        "email_id": "12345679",
        "inbox/outbox": "inbox",
        "sender/recipient": "mark@example.com",
        "subject": "Meeting Request",
        "sent_datetime": "2024-01-11 10:15:00",
        "body": "Can we schedule a meeting for next week?",
    }


def test_search_emails_no_results():
    """
    Tests search_emails with no results.
    """
    assert json.loads(email.search_emails("email_does_not_exist")) == []


def test_search_emails_result_limit():
    """
    Tests search_emails returns at most 5 results.
    """
    many_emails = [
        {
            "email_id": f"1234567{i}",
            "inbox/outbox": "inbox",
            "sender/recipient": "test@example.com",
            "subject": "Update",
            "sent_datetime": f"2024-01-{10 + i} 09:00:00",
            "body": "Content here.",
        }
        for i in range(7)
    ]
    _set_emails(many_emails)
    results = json.loads(email.search_emails("Update"))
    assert len(results) == 5


def test_send_email():
    """
    Tests send_email.
    """
    assert email.send_email("jane@example.com", "Reminder", "Meeting at 10am") == "Email sent successfully."
    # check that the email was added to the outbox
    state = get_state()
    assert state.emails["inbox/outbox"].values[-1] == "outbox"
    assert state.emails["sender/recipient"].values[-1] == "jane@example.com"
    assert state.emails["subject"].values[-1] == "Reminder"
    assert state.emails["body"].values[-1] == "Meeting at 10am"


def test_send_email_id_is_zero_padded_and_retrievable():
    previous_max = get_state().emails["email_id"].max()
    assert isinstance(previous_max, str)
    assert email.send_email("jane@example.com", "Reminder", "Meeting at 10am") == "Email sent successfully."
    new_id = get_state().emails["email_id"].values[-1]
    assert isinstance(new_id, str)
    assert len(new_id) == 8
    assert new_id.isdigit()
    assert int(new_id) == int(previous_max) + 1
    assert email.get_email_information_by_id(new_id, "subject") == json.dumps({"subject": "Reminder"})


def test_send_email_missing_args():
    """
    Tests send_email with missing arguments.
    """
    assert email.send_email() == "Recipient, subject, or body not provided."
    assert email.send_email("jane@example.com") == "Recipient, subject, or body not provided."


def test_delete_email():
    """
    Tests delete_email.
    """
    _set_emails(test_emails)
    assert email.delete_email("12345678") == "Email deleted successfully."
    assert "12345678" not in get_state().emails["email_id"].values


def test_delete_email_no_id_provided():
    """
    Tests delete_email with no email_id provided.
    """
    assert email.delete_email() == "Email ID not provided."


def test_delete_email_not_found():
    """
    Tests delete_email with an email_id that does not exist.
    """
    _set_emails(test_emails)
    assert email.delete_email("00000000") == "Email not found."


def test_forward_email():
    """
    Tests forward_email.
    """
    _set_emails(test_emails)
    assert email.forward_email("12345679", "example@email.com") == "Email forwarded successfully."
    # Check that the email was added to the outbox
    state = get_state()
    assert state.emails["inbox/outbox"].values[-1] == "outbox"
    assert state.emails["sender/recipient"].values[-1] == "example@email.com"
    assert state.emails["subject"].values[-1] == "FW: Meeting Request"
    assert state.emails["body"].values[-1] == "Can we schedule a meeting for next week?"


def test_forward_email_missing_args():
    """
    Tests forward_email with missing arguments.
    """
    assert email.forward_email() == "Email ID or recipient not provided."
    assert email.forward_email("12345679") == "Email ID or recipient not provided."
    assert email.forward_email(recipient="example@email.com") == ("Email ID or recipient not provided.")


def test_reply_email():
    """
    Tests reply_email.
    """
    _set_emails(test_emails)
    assert email.reply_email("12345678", "Thank you for the update.") == "Email replied successfully."
    # Check that the email was added to the outbox
    state = get_state()
    assert state.emails["inbox/outbox"].values[-1] == "outbox"
    assert state.emails["sender/recipient"].values[-1] == "jane@example.com"
    assert state.emails["subject"].values[-1] == "Project Update"
    assert state.emails["body"].values[-1] == "Thank you for the update."


def test_reply_email_missing_args():
    """
    Tests reply_email with missing arguments.
    """
    assert email.reply_email() == "Email ID or body not provided."
    assert email.reply_email("12345678") == "Email ID or body not provided."
    assert email.reply_email(body="Thank you for the update.") == "Email ID or body not provided."


def test_search_emails_date_min_filter():
    _set_emails(test_emails)
    results = json.loads(email.search_emails("", date_min="2024-01-11"))
    assert len(results) == 1
    assert results[0]["email_id"] == "12345679"


def test_search_emails_date_max_filter():
    _set_emails(test_emails)
    results = json.loads(email.search_emails("", date_max="2024-01-10"))
    assert len(results) == 1
    assert results[0]["email_id"] == "12345678"


def test_search_emails_date_range_filter():
    _set_emails(test_emails)
    results = json.loads(email.search_emails("", date_min="2024-01-10", date_max="2024-01-10"))
    assert len(results) == 1
    assert results[0]["email_id"] == "12345678"


def test_search_emails_date_range_no_results():
    _set_emails(test_emails)
    results = json.loads(email.search_emails("", date_min="2024-01-12", date_max="2024-01-15"))
    assert len(results) == 0
