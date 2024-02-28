import pandas as pd
import pytest

from src.tools import project_management

test_tasks = [
    {
        "task_id": "00000144",
        "task_name": "Add animation to modal window",
        "assigned_to_email": "Santiago.Martinez@company.com",
        "list_name": "Backlog",
        "due_date": "2023-11-28",
        "board": "Front end",
    },
    {
        "task_id": "00000044",
        "task_name": "Add authentication for cloud storage",
        "assigned_to_email": "Fatima.Khan@company.com",
        "list_name": "Backlog",
        "due_date": "2023-11-28",
        "board": "Back end",
    },
    {
        "task_id": "00000244",
        "task_name": "Create wireframe for landing page",
        "assigned_to_email": "Akira.Sato@company.com",
        "list_name": "Backlog",
        "due_date": "2023-11-28",
        "board": "Design",
    },
]


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Load test data
    project_management.PROJECT_TASKS = pd.DataFrame(test_tasks)
    # This will run before each test
    yield
    # Teardown: Reset state after each test
    project_management.reset_state()


def test_get_task_information_by_id():
    """
    Tests get_task_information_by_id.
    """
    task = project_management.get_task_information_by_id.func("00000144", "task_name")
    assert task == {"task_name": "Add animation to modal window"}


def test_get_task_information_missing_arguments():
    """
    Tests get_task_information_by_id with missing arguments.
    """
    assert project_management.get_task_information_by_id.func() == "Task ID not provided."
    assert project_management.get_task_information_by_id.func("00000144") == "Field not provided."


def test_get_task_information_by_id_field_not_found():
    """
    Tests get_task_information_by_id with a non-existent field.
    """
    task = project_management.get_task_information_by_id.func("00000144", "non_existent_field")
    assert task == "Field not found."


def test_create_task():
    """
    Tests create_task.
    """
    new_task_id = project_management.create_task.func(
        "Integrate API service with frontend", "Santiago.Martinez@company.com", "In Progress", "2023-06-01", "Front end"
    )
    assert len(new_task_id) == 8  # Check if the task_id is 8 digits long
    assert (
        project_management.PROJECT_TASKS.loc[
            project_management.PROJECT_TASKS["task_id"] == new_task_id, "task_name"
        ].values[0]
        == "Integrate API service with frontend"
    )


def test_create_task_missing_args():
    """
    Tests create_task with missing arguments.
    """
    assert project_management.create_task.func() == "Missing task details."


def test_delete_task():
    """
    Tests delete_task.
    """
    message = project_management.delete_task.func("00000144")
    assert message == "Task deleted successfully."
    assert "00000144" not in project_management.PROJECT_TASKS["task_id"].values


def test_delete_task_no_id_provided():
    """
    Tests delete_task with no task_id provided.
    """
    message = project_management.delete_task.func()
    assert message == "Task ID not provided."


def test_delete_task_not_found():
    """
    Tests delete_task with a task_id that does not exist.
    """
    message = project_management.delete_task.func("non_existent_id")
    assert message == "Task not found."


def test_update_task():
    """
    Tests update_task.
    """
    message = project_management.update_task.func("00000144", "task_name", "Updated Task Name")
    assert message == "Task updated successfully."
    assert (
        project_management.PROJECT_TASKS.loc[
            project_management.PROJECT_TASKS["task_id"] == "00000144", "task_name"
        ].values[0]
        == "Updated Task Name"
    )


def test_update_task_no_id_provided():
    """
    Tests update_task with missing arguments.
    """
    message = project_management.update_task.func(None, "task_name", "New Task Name")
    assert message == "Task ID, field, or new value not provided."


def test_update_task_not_found():
    """
    Tests update_task with a task_id that does not exist.
    """
    message = project_management.update_task.func("non_existent_id", "task_name", "New Task Name")
    assert message == "Task not found."


def test_search_tasks():
    """
    Tests search_tasks.
    """
    tasks = project_management.search_tasks.func("Add", "Santiago", "Backlog", "2023-11-28", "Front end")
    assert tasks == [test_tasks[0]]


def test_search_tasks_no_params():
    """
    Tests search_tasks with no parameters.
    """
    tasks = project_management.search_tasks.func()
    assert tasks == "No search parameters provided."


def test_search_tasks_no_results():
    """
    Tests search_tasks with no results.
    """
    tasks = project_management.search_tasks.func(
        "non_existent_task", "non_existent_email", "non_existent_list", "2023-11-29", "non_existent_board"
    )
    assert tasks == []


def test_search_tasks_multiple_results():
    """
    Tests search_tasks with multiple results.
    """
    tasks = project_management.search_tasks.func(due_date="2023-11-28")
    assert tasks == test_tasks
