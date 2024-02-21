import pandas as pd
from scripts.data_generation.mocked_data.generate_project_management_data import sales_team_emails, project_management_team_emails

project_management_data = pd.read_csv("data/processed/project_tasks.csv")


def test_no_two_tasks_same_name_same_person():
    """
    Tests that no two tasks with the same name are assigned to the same person.
    """
    grouped = project_management_data.groupby(["task_name", "assigned_to"]).size()
    assert len(grouped[grouped > 1]) == 0

def test_no_sales_team_in_project_management_system():
    """
    Tests that there are no sales team members in the project management system.
    """
    assert not project_management_data["assigned_to"].isin(sales_team_emails).any()

def all_project_management_team_members_have_tasks():
    """
    Tests that all project management team members have tasks assigned to them.
    """
    assert project_management_data["assigned_to"].isin(project_management_team_emails).all()
