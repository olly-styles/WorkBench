import pandas as pd
import pytest

from src.tools import email

# Sample data for emails
test_emails = [
    {
        "email_id": "12345678",
        "sender": "jane@example.com",
        "subject": "Project Update",
        "sent_date": "2024-01-10 09:30:00",
        "body": "Please find the project update attached.",
    },
    {
        "email_id": "12345679",
        "sender": "mark@example.com",
        "subject": "Meeting Request",
        "sent_date": "2024-01-11 10:15:00",
        "body": "Can we schedule a meeting for next week?",
    },
]
email.EMAILS = pd.DataFrame(test_emails)


def test_get_email_information_by_id():
    """
    Tests get_email_information_by_id.
    """
    assert email.get_email_information_by_id.func("12345678", "subject") == {
        "subject": "Project Update"
    }


def test_get_email_information_missing_arguments():
    """
    Tests get_email_information_by_id with no ID and no field.
    """
    assert email.get_email_information_by_id.func() == "Email ID not provided."
    assert email.get_email_information_by_id.func("12345678") == "Field not provided."


def test_get_email_information_by_id_field_not_found():
    """
    Tests get_email_information_by_id with field not found.
    """
    result = email.get_email_information_by_id.func("12345678", "field_does_not_exist")
    assert result == "Field not found."


def test_search_emails():
    """
    Tests search_emails.
    """
    assert email.search_emails.func("Meeting Request")[0] == {
        "email_id": "12345679",
        "subject": "Meeting Request",
        "sender": "mark@example.com",
        "sent_date": "2024-01-11 10:15:00",
        "body": "Can we schedule a meeting for next week?",
    }


def test_search_emails_no_results():
    """
    Tests search_emails with no results.
    """
    assert email.search_emails.func("email_does_not_exist") == "No emails found."


def test_send_email():
    """
    Tests send_email.
    """
    assert (
        email.send_email.func("jane@example.com", "Reminder", "Meeting at 10am")
        == "Email sent successfully."
    )


def test_send_email_missing_args():
    """
    Tests send_email with missing arguments.
    """
    assert email.send_email.func() == "Recipient, subject, or body not provided."
    assert (
        email.send_email.func("jane@example.com")
        == "Recipient, subject, or body not provided."
    )


def test_delete_email():
    """
    Tests delete_email.
    """
    assert email.delete_email.func("12345678") == "Email deleted successfully."
    assert "12345678" not in email.EMAILS["email_id"].values


def test_delete_email_no_id_provided():
    """
    Tests delete_email with no email_id provided.
    """
    assert email.delete_email.func() == "Email ID not provided."


def test_delete_email_not_found():
    """
    Tests delete_email with an email_id that does not exist.
    """
    assert email.delete_email.func("00000000") == "Email not found."


def test_forward_email():
    """
    Tests forward_email.
    """
    assert (
        email.forward_email.func("12345679", "example@email.com")
        == "Email forwarded successfully."
    )


def test_forward_email_missing_args():
    """
    Tests forward_email with missing arguments.
    """
    assert email.forward_email.func() == "Email ID or recipient not provided."
    assert email.forward_email.func("12345679") == "Email ID or recipient not provided."
    assert email.forward_email.func(recipient="example@email.com") == (
        "Email ID or recipient not provided."
    )
