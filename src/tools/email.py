import json

import pandas as pd

from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME
from src.tools._utils import (
    DEFAULT_SEARCH_RESULT_LIMIT,
    delete_record,
    generate_next_id,
    get_record_field,
    normalize_email,
    validate_email,
)
from src.tools.state import get_state
from src.tools.tool import tool


@tool("email.get_email_information_by_id")
def get_email_information_by_id(email_id: str | None = None, field: str | None = None) -> str:
    """
    Retrieves specific details of an email by its ID.

    Parameters
    ----------
    email_id : str, optional
        Unique ID of the email.
    field : str, optional
        Specific field to return. Available fields: "email_id", "sender", "subject", "sent_date", "body", "inbox/outbox".

    Returns
    -------
    email_information : dict
        Information of the specified email for the given ID and field.

    Examples
    --------
    >>> email.get_email_information_by_id("12345678", "subject")
    {{"subject": "Project Update"}}

    >>> email.get_email_information_by_id("12345678", "sent_date")
    {{"sent_date": "2024-01-10 09:30:00"}}
    """
    return get_record_field(get_state().emails, "email_id", email_id, field, "Email")


@tool("email.search_emails")
def search_emails(query: str = "", date_min: str | None = None, date_max: str | None = None) -> str:
    """
    Searches for emails matching the given query across subject, body, or sender fields.
    The function matches an email if all words in the query appear in any of these fields.

    Parameters
    ----------
    query : str, optional
        Search query, matching terms in subject, body, or sender fields.
    date_min : str, optional
        Lower date limit for the email's sent date (inclusive). Format: "YYYY-MM-DD"
    date_max : str, optional
        Upper date limit for the email's sent date (inclusive). Format: "YYYY-MM-DD"

    Returns
    -------
    emails : list
        List of emails matching the query criteria. Returns at most 5 emails.

    Examples
    --------
    >>> email.search_emails("Project Update")
    [{{"email_id": "12345678", "inbox/outbox": "inbox", "subject": "Project Update", "sender/recipient": "jane@example.com", "sent_datetime": "2024-01-10 09:30:00", "body": "Please find the project update attached."}}]
    """
    state = get_state()
    query_words = query.lower().split()

    # Filter function to check if all query words are in any of the specified fields
    def filter_emails(row: pd.Series) -> bool:
        combined_fields = f"{row['subject']} {row['body']} {row['sender/recipient']}".lower()
        return all(word in combined_fields for word in query_words)

    # Apply filter function across all rows
    filtered_df = state.emails[state.emails.apply(filter_emails, axis=1)].copy()
    filtered_df["sent_datetime"] = pd.to_datetime(filtered_df["sent_datetime"])
    if date_min:
        filtered_df = filtered_df[filtered_df["sent_datetime"].dt.date >= pd.Timestamp(date_min).date()]
    if date_max:
        filtered_df = filtered_df[filtered_df["sent_datetime"].dt.date <= pd.Timestamp(date_max).date()]
    filtered_df = filtered_df.sort_values("sent_datetime", ascending=False)
    filtered_df["sent_datetime"] = filtered_df["sent_datetime"].astype(str)
    return json.dumps(filtered_df.to_dict(orient="records")[:DEFAULT_SEARCH_RESULT_LIMIT])


@tool("email.send_email")
def send_email(recipient: str | None = None, subject: str | None = None, body: str | None = None) -> str:
    """
    Sends an email to the specified recipient.

    Parameters
    ----------
    recipient : str, optional
        Email address of the recipient.
    subject : str, optional
        Subject line of the email.
    body : str, optional
        Body content of the email.

    Returns
    -------
    message : str
        Confirmation message of the email being sent.

    Examples
    --------
    >>> email.send_email("jane@example.com", "Meeting Reminder", "Don't forget our meeting at 10am tomorrow.")
    "Email sent successfully."
    """
    state = get_state()
    if not recipient or not subject or not body:
        return "Recipient, subject, or body not provided."
    if not validate_email(recipient):
        return "Invalid recipient email address."
    recipient = normalize_email(recipient)

    email_id = generate_next_id(state.emails, "email_id")
    sent_datetime = HARDCODED_CURRENT_TIME
    new_row = pd.DataFrame(
        {
            "email_id": [email_id],
            "inbox/outbox": ["outbox"],
            "sender/recipient": [recipient],
            "subject": [subject],
            "sent_datetime": [sent_datetime],
            "body": [body],
        }
    )
    state.emails = pd.concat([state.emails, new_row], ignore_index=True)

    return "Email sent successfully."


@tool("email.delete_email")
def delete_email(email_id: str | None = None) -> str:
    """
    Deletes an email by its ID.

    Parameters
    ----------
    email_id : str, optional
        Unique ID of the email to be deleted.

    Returns
    -------
    message : str
        Message indicating whether the deletion was successful.

    Examples
    --------
    >>> email.delete_email("12345678")
    "Email deleted successfully."
    """
    state = get_state()
    state.emails, message = delete_record(state.emails, "email_id", email_id, "Email")
    return message


@tool("email.forward_email")
def forward_email(email_id: str | None = None, recipient: str | None = None) -> str:
    """
    Forwards an email to the specified recipient.

    Parameters
    ----------
    email_id : str, optional
        Unique ID of the email to be forwarded.
    recipient : str, optional
        Email address of the recipient.

    Returns
    -------
    message : str
        Message indicating whether the email was forwarded successfully.

    Examples
    --------
    >>> email.forward_email("12345678", "jane@example.com")
    "Email forwarded successfully."
    """
    state = get_state()
    if not email_id or not recipient:
        return "Email ID or recipient not provided."
    if email_id not in state.emails["email_id"].values:
        return "Email not found."
    if not validate_email(recipient):
        return "Invalid recipient email address."
    recipient = normalize_email(recipient)
    email = state.emails[state.emails["email_id"] == email_id].to_dict(orient="records")[0]
    result = send_email(recipient, f"FW: {email['subject']}", email["body"])
    return "Email forwarded successfully." if result == "Email sent successfully." else result


@tool("email.reply_email")
def reply_email(email_id: str | None = None, body: str | None = None) -> str:
    """
    Replies to an email by its ID.

    Parameters
    ----------
    email_id : str, optional
        Unique ID of the email to be replied.
    body : str, optional
        Body content of the email.

    Returns
    -------
    message : str
        Confirmation message of the email being replied.

    Examples
    --------
    >>> email.reply_email("12345678", "Thank you for the update.")
    "Email replied successfully."
    """
    state = get_state()
    if not email_id or not body:
        return "Email ID or body not provided."
    if email_id not in state.emails["email_id"].values:
        return "Email not found."
    email = state.emails[state.emails["email_id"] == email_id].to_dict(orient="records")[0]
    result = send_email(email["sender/recipient"], email["subject"], body)
    return "Email replied successfully." if result == "Email sent successfully." else result
