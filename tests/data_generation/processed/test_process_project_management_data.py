import pandas as pd

project_management_data = pd.read_csv("data/processed/project_tasks.csv")

def test_no_two_tasks_same_name_same_person():
    """
    Tests that no two tasks with the same name are assigned to the same person.
    """
    grouped = project_management_data.groupby(["task_name", "assigned_to"]).size()
    assert len(grouped[grouped > 1]) == 0
