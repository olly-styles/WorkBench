import pandas as pd
from langchain.tools import tool

EMAILS = pd.read_csv("data/processed/emails.csv", dtype=str)


@tool("email.get_email_information_by_id", return_direct=False)
def get_email_information_by_id(email_id=None, field=None):
    """
    Retrieves specific details of an email by its ID.

    Parameters
    ----------
    email_id : str, optional
        Unique ID of the email.
    field : str, optional
        Specific field to return. Available fields: "email_id", "sender", "subject", "sent_date", "body"

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
    if not email_id:
        return "Email ID not provided."
    if not field:
        return "Field not provided."
    email = EMAILS[EMAILS["email_id"] == email_id].to_dict(orient="records")
    if email:
        if field in email[0]:
            return {field: email[0][field]}
        else:
            return "Field not found."
    else:
        return "Email not found."


@tool("email.search_emails", return_direct=False)
def search_emails(query="", date_min=None, date_max=None):
    """
    Searches for emails matching the given query.

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
        List of emails matching the query criteria.

    Examples
    --------
    >>> email.search_emails("Project Update")
    [{{"email_id": "12345678", "subject": "Project Update", "sender": "jane@example.com", "sent_date": "2024-01-10 09:30:00", "body": "Please find the project update attached."}}]
    """
    emails = EMAILS[
        (EMAILS["subject"].str.contains(query))
        | (EMAILS["body"].str.contains(query))
        | (EMAILS["sender"].str.contains(query))
    ].to_dict(orient="records")
    if date_min:
        emails = [
            email
            for email in emails
            if pd.Timestamp(email["sent_date"]) >= pd.Timestamp(date_min)
        ]
    if date_max:
        emails = [
            email
            for email in emails
            if pd.Timestamp(email["sent_date"]) <= pd.Timestamp(date_max)
        ]
    if emails:
        return emails[:5]
    else:
        return "No emails found."


@tool("email.send_email", return_direct=False)
def send_email(recipient=None, subject=None, body=None):
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
    if not recipient or not subject or not body:
        return "Recipient, subject, or body not provided."

    return "Email sent successfully."


@tool("email.delete_email", return_direct=False)
def delete_email(email_id=None):
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
    global EMAILS

    if not email_id:
        return "Email ID not provided."

    if email_id in EMAILS["email_id"].values:
        EMAILS = EMAILS[EMAILS["email_id"] != email_id]
        return "Email deleted successfully."
    else:
        return "Email not found."
