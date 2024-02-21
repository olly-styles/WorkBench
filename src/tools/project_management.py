import pandas as pd
from langchain.tools import tool

# Data is hard-coded so that the agent can call them without passing the dataframe as an argument.
# We cannot use a class because LangChain does not support tools inside classes.
PROJECT_TASKS = pd.read_csv("data/processed/project_tasks.csv", dtype=str)


def reset_state():
    """
    Resets the project tasks to the original state.
    """
    global PROJECT_TASKS
    PROJECT_TASKS = pd.read_csv("data/processed/project_tasks.csv", dtype=str)


@tool("project_management.get_task_information_by_id", return_direct=False)
def get_task_information_by_id(task_id=None, field=None):
    """
    Returns the task infomration for a given ID.

    Parameters
    ----------
    task_id : str, optional
        8-digit ID of the task.
    field : str, optional
        Field to return. Available fields are: "task_id", "task_name", "assigned_to", "list_name", "due_date", "board"

    Returns
    -------
    task : dict
        Task information for the given ID and field.

    Examples
    --------
    >>> project_management.get_task_information_by_id("00000000", "task_name")
    {{"task_name": "Refactor code"}}
    """
    if not task_id:
        return "Task ID not provided."
    if not field:
        return "Field not provided."
    task = PROJECT_TASKS[PROJECT_TASKS["task_id"] == task_id].to_dict(orient="records")
    if task:
        if field in task[0]:
            return {field: task[0][field]}
        else:
            return "Field not found."
    else:
        return "Task not found."


@tool("project_management.search_tasks", return_direct=False)
def search_tasks(task_name=None, assigned_to=None, list_name=None, due_date=None, board=None):
    """
    Searches for tasks based on the given parameters.

    Parameters
    ----------
    task_name : str, optional
        Name of the task.
    assigned_to : str, optional
        Email address of the person assigned to the task.
    list_name : str, optional
        Name of the list the task belongs to.
    due_date : str, optional
        Due date of the task in "YYYY-MM-DD" format.
    board : str, optional
        Name of the board the task belongs to.

    Returns
    -------
    tasks : dict
        Task information for the given parameters.

    Examples
    --------
    >>> project_management.search_tasks("Refactor code", "tishtrya@example.com" "In progress", "2023-06-01", "Front end")
    {{"task_id": "00000000", "task_name": "Refactor code", "assigned_to": "tishtrya@example.com", "list_name": "In progress", "due_date": "2023-06-01", "board": "Front end"}}
    """
    if not any([task_name, assigned_to, list_name, due_date, board]):
        return "No search parameters provided."
    tasks = PROJECT_TASKS.copy()
    if task_name:
        tasks = tasks[tasks["task_name"].str.contains(task_name, case=False)]
    if assigned_to:
        tasks = tasks[tasks["assigned_to"].str.contains(assigned_to, case=False)]
    if list_name:
        tasks = tasks[tasks["list_name"].str.contains(list_name, case=False)]
    if due_date:
        tasks = tasks[tasks["due_date"].str.contains(due_date, case=False)]
    if board:
        tasks = tasks[tasks["board"].str.contains(board, case=False)]
    return tasks.to_dict(orient="records")


@tool("project_management.create_task", return_direct=False)
def create_task(task_name=None, assigned_to=None, list_name=None, due_date=None, board=None):
    """
    Creates a new task.

    Parameters
    ----------
    task_name : str
        Name of the task.
    assigned_to : str
        Email address of the person assigned to the task.
    list_name : str
        Name of the list the task belongs to.
    due_date : str
        Due date of the task in "YYYY-MM-DD" format.
    board : str
        Name of the board the task belongs to.

    Returns
    -------
    task_id : str
        8-digit ID of the new task.

    Examples
    --------
    >>> project_management.create_task("Integrate API service with frontend", "sam@example.com", "In progress", "2023-06-01", "Front end")
    "00000001"
    """
    global PROJECT_TASKS

    if not all([task_name, assigned_to, list_name, due_date, board]):
        return "Missing task details."
    
    if assigned_to not in PROJECT_TASKS["assigned_to"].values:
        return "Assignee email not valid. Please choose from the list of team members."
    if list_name not in ["Backlog", "In Progress", "In Review", "Completed"]:
        return "List not valid. Please choose from: 'Backlog', 'In Progress', 'In Review', 'Completed'."
    if board not in ["Back end", "Front end", "Design"]:
        return "Board not valid. Please choose from: 'Back end', 'Front end', 'Design'."

    task_id = str(int(PROJECT_TASKS["task_id"].max()) + 1).zfill(8)
    new_task = pd.DataFrame(
        {
            "task_id": [task_id],
            "task_name": [task_name],
            "assigned_to": [assigned_to],
            "list_name": [list_name],
            "due_date": [due_date],
            "board": [board],
        }
    )
    PROJECT_TASKS = pd.concat([PROJECT_TASKS, new_task], ignore_index=True)
    return task_id


@tool("project_management.delete_task", return_direct=False)
def delete_task(task_id=None):
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
    global PROJECT_TASKS

    if not task_id:
        return "Task ID not provided."

    if task_id in PROJECT_TASKS["task_id"].values:
        PROJECT_TASKS = PROJECT_TASKS[PROJECT_TASKS["task_id"] != task_id]
        return "Task deleted successfully."
    else:
        return "Task not found."


@tool("project_management.update_task", return_direct=False)
def update_task(task_id=None, field=None, new_value=None):
    """
    Updates a task by ID.

    Parameters
    ----------
    task_id : str
        8-digit ID of the task.
    field : str
        Field to update. Available fields are: "task_name", "assigned_to", "list_name", "due_date", "board"
    new_value : str
        New value for the field.

    Returns
    -------
    message : str
        Message indicating the status of the update.

    Examples
    --------
    >>> project_management.update_task("00000000", "task_name", "New Task Name")
    "Task updated successfully."
    """
    global PROJECT_TASKS

    if not task_id or not field or not new_value:
        return "Task ID, field, or new value not provided."
    
    if field == "board" and new_value not in ["Back end", "Front end", "Design"]:
        return "Board not valid. Please choose from: 'Back end', 'Front end', 'Design'."
    if field == "list_name" and new_value not in ["Backlog", "In Progress", "In Review", "Completed"]:
        return "List not valid. Please choose from: 'Backlog', 'In Progress', 'In Review', 'Completed'."
    if field == "assigned_to" and new_value not in PROJECT_TASKS["assigned_to"].values:
        return "Assignee email not valid. Please choose from the list of team members."        
    
    if task_id in PROJECT_TASKS["task_id"].values:
        if field in PROJECT_TASKS.columns:
            PROJECT_TASKS.loc[PROJECT_TASKS["task_id"] == task_id, field] = new_value
            return "Task updated successfully."
        else:
            return "Field not valid."
    else:
        return "Task not found."
