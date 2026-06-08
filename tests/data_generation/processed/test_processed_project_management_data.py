import pandas as pd

import scripts.data_generation.sandbox_databases.generate_project_management_data as pm_data

pm_data.load_team_emails()
project_management_data = pd.read_csv("data/processed/project_tasks.csv")


def test_no_two_tasks_same_name_same_person():
    """
    Tests that no two tasks with the same name are assigned to the same person.
    """
    grouped = project_management_data.groupby(["task_name", "assigned_to_email"]).size()
    assert len(grouped[grouped > 1]) == 0


def test_no_sales_team_in_project_management_system():
    """
    Tests that there are no sales team members in the project management system.
    """
    assert not project_management_data["assigned_to_email"].isin(pm_data.sales_team_emails).any()


def test_all_project_management_team_members_have_tasks():
    """
    Tests that all project management team members have tasks assigned to them.
    """
    assigned_emails = set(project_management_data["assigned_to_email"])
    assert set(pm_data.project_management_team_emails).issubset(assigned_emails)
