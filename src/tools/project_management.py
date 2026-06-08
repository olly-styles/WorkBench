import json

import pandas as pd

from src.tools._utils import (
    delete_record,
    generate_next_id,
    get_record_field,
    normalize_email,
)
from src.tools.state import get_state
from src.tools.tool import tool

VALID_LISTS = ["Backlog", "In Progress", "In Review", "Completed"]
VALID_BOARDS = ["Back end", "Front end", "Design"]
SEARCH_TASKS_RESULT_LIMIT = 200


@tool("project_management.get_task_information_by_id")
def get_task_information_by_id(task_id: str | None = None, field: str | None = None) -> str:
    """
    Returns the task infomration for a given ID.

    Parameters
    ----------
    task_id : str, optional
        8-digit ID of the task.
    field : str, optional
        Field to return. Available fields are: "task_id", "task_name", "assigned_to_email", "list_name", "due_date", "board"

    Returns
    -------
    task : dict
        Task information for the given ID and field.

    Examples
    --------
    >>> project_management.get_task_information_by_id("00000000", "task_name")
    {{"task_name": "Refactor code"}}
    """
    return get_record_field(get_state().project_tasks, "task_id", task_id, field, "Task")


@tool("project_management.search_tasks")
def search_tasks(
    task_name: str | None = None,
    assigned_to_email: str | None = None,
    list_name: str | None = None,
    due_date: str | None = None,
    board: str | None = None,
) -> str:
    """
    Searches for tasks based on the given parameters.

    Parameters
    ----------
    task_name : str, optional
        Name of the task.
    assigned_to_email : str, optional
        Email address of the person assigned to the task.
    list_name : str, optional
        Name of the list the task belongs to. One of: "Backlog", "In Progress", "In Review", "Completed".
    due_date : str, optional
        Due date of the task in "YYYY-MM-DD" format.
    board : str, optional
        Name of the board the task belongs to. One of: "Back end", "Front end", "Design".

    Returns
    -------
    tasks : list
        List of tasks matching the given parameters. Returns at most 200 tasks.

    Examples
    --------
    >>> project_management.search_tasks("Refactor code", "tishtrya@example.com" "In progress", "2023-06-01", "Front end")
    {{"task_id": "00000000", "task_name": "Refactor code", "assigned_to_email": "tishtrya@example.com", "list_name": "In Progress", "due_date": "2023-06-01", "board": "Front End"}}
    """
    if not any((task_name, assigned_to_email, list_name, due_date, board)):
        return "No search parameters provided."
    tasks = get_state().project_tasks.copy()
    if task_name:
        tasks = tasks[tasks["task_name"].str.contains(task_name, regex=False)]
    if assigned_to_email:
        tasks = tasks[tasks["assigned_to_email"].str.contains(assigned_to_email, regex=False)]
    if list_name:
        tasks = tasks[tasks["list_name"].str.contains(list_name, regex=False)]
    if due_date:
        tasks = tasks[tasks["due_date"].str.contains(due_date, regex=False)]
    if board:
        tasks = tasks[tasks["board"].str.contains(board, regex=False)]
    results = tasks.to_dict(orient="records")
    return json.dumps(results[:SEARCH_TASKS_RESULT_LIMIT])


@tool("project_management.create_task")
def create_task(
    task_name: str | None = None,
    assigned_to_email: str | None = None,
    list_name: str | None = None,
    due_date: str | None = None,
    board: str | None = None,
) -> str:
    """
    Creates a new task.

    Parameters
    ----------
    task_name : str
        Name of the task.
    assigned_to_email : str
        Email address of the person assigned to the task.
    list_name : str
        Name of the list the task belongs to. One of: "Backlog", "In Progress", "In Review", "Completed".
    due_date : str
        Due date of the task in "YYYY-MM-DD" format.
    board : str
        Name of the board the task belongs to. One of: "Back end", "Front end", "Design".

    Returns
    -------
    task_id : str
        8-digit ID of the new task.

    Examples
    --------
    >>> project_management.create_task("Integrate API service with frontend", "sam@example.com", "In progress", "2023-06-01", "Front end")
    "00000001"
    """
    state = get_state()

    if not all((task_name, assigned_to_email, list_name, due_date, board)):
        return "Missing task details."

    assert assigned_to_email is not None
    assigned_to_email = normalize_email(assigned_to_email)
    if assigned_to_email not in state.project_tasks["assigned_to_email"].str.lower().values:
        return "Assignee email not valid. Please choose from the list of team members."
    if list_name not in VALID_LISTS:
        return f"List not valid. Please choose from: {', '.join(repr(v) for v in VALID_LISTS)}."
    if board not in VALID_BOARDS:
        return f"Board not valid. Please choose from: {', '.join(repr(v) for v in VALID_BOARDS)}."

    task_id = generate_next_id(state.project_tasks, "task_id")
    new_task = pd.DataFrame(
        {
            "task_id": [task_id],
            "task_name": [task_name],
            "assigned_to_email": [assigned_to_email],
            "list_name": [list_name],
            "due_date": [due_date],
            "board": [board],
        }
    )
    state.project_tasks = pd.concat([state.project_tasks, new_task], ignore_index=True)
    return task_id


@tool("project_management.delete_task")
def delete_task(task_id: str | None = None) -> str:
    """
    Deletes a task by ID.

    Parameters
    ----------
    task_id : str
        8-digit ID of the task.

    Returns
    -------
    message : str
        Message indicating the status of the deletion.

    Examples
    --------
    >>> project_management.delete_task("00000000")
    "Task deleted successfully."
    """
    state = get_state()
    state.project_tasks, message = delete_record(state.project_tasks, "task_id", task_id, "Task")
    return message


@tool("project_management.update_task")
def update_task(task_id: str | None = None, field: str | None = None, new_value: str | None = None) -> str:
    """
    Updates a task by ID.

    Parameters
    ----------
    task_id : str
        8-digit ID of the task.
    field : str
        Field to update. Available fields are: "task_name", "assigned_to_email", "list_name", "due_date", "board"
    new_value : str
        New value for the field. When field is "list_name", one of: "Backlog", "In Progress", "In Review", "Completed". When field is "board", one of: "Back end", "Front end", "Design".

    Returns
    -------
    message : str
        Message indicating the status of the update.

    Examples
    --------
    >>> project_management.update_task("00000000", "task_name", "New Task Name")
    "Task updated successfully."
    """
    state = get_state()

    if not task_id or not field or not new_value:
        return "Task ID, field, or new value not provided."

    if field == "assigned_to_email":
        new_value = normalize_email(new_value)

    if field == "board" and new_value not in VALID_BOARDS:
        return f"Board not valid. Please choose from: {', '.join(repr(v) for v in VALID_BOARDS)}."
    if field == "list_name" and new_value not in VALID_LISTS:
        return f"List not valid. Please choose from: {', '.join(repr(v) for v in VALID_LISTS)}."
    if field == "assigned_to_email" and new_value not in state.project_tasks["assigned_to_email"].str.lower().values:
        return "Assignee email not valid. Please choose from the list of team members."

    if task_id not in state.project_tasks["task_id"].values:
        return "Task not found."
    if field not in state.project_tasks.columns:
        return "Field not valid."
    state.project_tasks.loc[state.project_tasks["task_id"] == task_id, field] = new_value
    return "Task updated successfully."
