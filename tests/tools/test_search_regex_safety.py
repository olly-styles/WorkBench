import json

import pandas as pd
import pytest

from src.tools import calendar, company_directory, project_management
from src.tools import customer_relationship_manager as crm
from src.tools.state import get_state, reset_state


@pytest.fixture(autouse=True)
def reset_tool_state():
    reset_state()
    yield
    reset_state()


def test_calendar_search_handles_regex_metacharacters():
    get_state().calendar_events = pd.DataFrame(
        [
            {
                "event_id": "00000000",
                "event_name": "Sprint [Q1]",
                "participant_email": "a@company.com",
                "event_start": "2023-10-01 10:00:00",
                "duration": "60",
            }
        ]
    )
    results = json.loads(calendar.search_events.func("[Q1"))
    assert len(results) == 1
    assert results[0]["event_name"] == "Sprint [Q1]"


def test_crm_search_handles_regex_metacharacters():
    get_state().crm_data = pd.DataFrame(
        [
            {
                "customer_id": "00000001",
                "customer_name": "ACME (US) Inc.",
                "assigned_to_email": "email1@test.com",
                "customer_email": "c1@test.com",
                "customer_phone": "123",
                "last_contact_date": "2023-01-01",
                "product_interest": "Software",
                "status": "Qualified",
                "notes": "",
                "follow_up_by": "2023-01-15",
            }
        ]
    )
    results = json.loads(crm.search_customers.func(customer_name="(US)"))
    assert len(results) == 1
    assert results[0]["customer_name"] == "ACME (US) Inc."


def test_project_management_search_handles_regex_metacharacters():
    get_state().project_tasks = pd.DataFrame(
        [
            {
                "task_id": "00000001",
                "task_name": "Fix (login) bug",
                "assigned_to_email": "a@company.com",
                "list_name": "Backlog",
                "due_date": "2023-11-28",
                "board": "Back end",
            }
        ]
    )
    results = json.loads(project_management.search_tasks.func(task_name="(login"))
    assert len(results) == 1
    assert results[0]["task_name"] == "Fix (login) bug"


def test_company_directory_search_handles_regex_metacharacters():
    get_state().directory_emails = pd.DataFrame(["a.b+test@atlas.com"], columns=pd.Index(["email_address"]))
    assert company_directory.find_email_address.func("b+test") == json.dumps(["a.b+test@atlas.com"])
    assert company_directory.find_email_address.func("[") == "No employee found with that name."
