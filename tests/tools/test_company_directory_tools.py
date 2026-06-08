import json

import pandas as pd

from src.tools import company_directory
from src.tools.state import get_state


def _set_directory(emails: list[str]):
    get_state().directory_emails = pd.DataFrame(emails, columns=pd.Index(["email_address"]))


def test_find_email_by_first_name():
    _set_directory(["alice.smith@atlas.com", "bob.jones@atlas.com"])
    result = company_directory.find_email_address.func("alice")
    assert result == json.dumps(["alice.smith@atlas.com"])


def test_find_email_by_last_name():
    _set_directory(["alice.smith@atlas.com", "bob.jones@atlas.com"])
    result = company_directory.find_email_address.func("jones")
    assert result == json.dumps(["bob.jones@atlas.com"])


def test_find_email_case_insensitive():
    _set_directory(["alice.smith@atlas.com"])
    result = company_directory.find_email_address.func("Alice")
    assert result == json.dumps(["alice.smith@atlas.com"])


def test_find_email_multiple_matches():
    _set_directory(["alice.smith@atlas.com", "alice.jones@atlas.com"])
    result = company_directory.find_email_address.func("alice")
    assert result == json.dumps(["alice.smith@atlas.com", "alice.jones@atlas.com"])


def test_find_email_no_match():
    _set_directory(["alice.smith@atlas.com"])
    result = company_directory.find_email_address.func("bob")
    assert result == "No employee found with that name."


def test_find_email_empty_name():
    _set_directory(["alice.smith@atlas.com"])
    result = company_directory.find_email_address.func("")
    assert result == "Name not provided."


def test_find_email_no_name_arg():
    _set_directory(["alice.smith@atlas.com"])
    result = company_directory.find_email_address.func()
    assert result == "Name not provided."
