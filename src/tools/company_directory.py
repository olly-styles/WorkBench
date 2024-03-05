import pandas as pd
from langchain.tools import tool

EMAILS = pd.read_csv("data/raw/email_addresses.csv", header=None, names=["email_address"])

@tool("company_directory.find_email_address", return_direct=False)
def find_email_address_by_name(name=""):
    """
    Finds the email address of an employee by their name.
    
    Parameters
    ----------
    name : str, optional
        Name of the person.
    
    Returns
    -------
    email_address : str
        Email addresses of the person.
    
    Examples
    --------
    >>> directory.find_email_address_by_name("John")
    "john.smith@example.com"
    """
    global EMAILS
    if name == "":
        return "Name not provided."
    name = name.lower()
    email_address = EMAILS[EMAILS["email_address"].str.contains(name)]
    return email_address["email_address"].values    