import json

from src.tools.state import get_state
from src.tools.tool import tool


@tool("company_directory.find_email_address")
def find_email_address(name: str = "") -> str:
    """
    Finds the email address of an employee by their name.

    Parameters
    ----------
    name : str, optional
        Name of the person.

    Returns
    -------
    email_address : list[str]
        Email addresses of the person.

    Examples
    --------
    >>> directory.find_email_address("John")
    ["john.smith@example.com"]
    """
    state = get_state()
    if not name:
        return "Name not provided."
    results = state.directory_emails[state.directory_emails["email_address"].str.contains(name.lower(), regex=False)][
        "email_address"
    ].values.tolist()
    return json.dumps(results) if results else "No employee found with that name."
