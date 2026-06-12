import random
from typing import Any

import pandas as pd

import scripts.data_generation.sandbox_databases.generate_project_management_data as pm_data
from src.data_generation.data_generation_utils import (
    HARDCODED_CURRENT_TIME,
    generate_and_write_tasks_and_outcomes,
    get_first_name,
    get_natural_language_date,
    random_choice_excluding,
)

project_tasks: Any = None
emails: Any = None
task_names: Any = None
boards: Any = None


def load_data() -> None:
    global project_tasks, emails, task_names, boards
    if project_tasks is not None:
        return
    pm_data.load_team_emails()
    project_tasks = pd.read_csv("data/processed/project_tasks.csv", dtype=str)
    emails = project_tasks["assigned_to_email"].unique()
    task_names = project_tasks["task_name"].unique()
    boards = project_tasks["board"].unique()


def get_random_task_dict() -> dict:
    task = random.choice(task_names)
    email = random.choice(emails)
    board = random.choice(boards)
    due_date = str(HARDCODED_CURRENT_TIME.date() + pd.Timedelta(days=random.randint(1, 7)))
    natural_language_due_date = get_natural_language_date(due_date)
    return {
        "task_name": task,
        "email": email,
        "board": board,
        "due_date": due_date,
        "natural_language_due_date": natural_language_due_date,
        "name": get_first_name(email),
    }


def get_new_task_string(task_name: str, email: str, board: str, due_date: str) -> str:
    return f"""project_management.create_task.func(task_name="{task_name}", board="{board}", assigned_to_email="{email}", due_date="{due_date}", list_name="Backlog")"""


def move_tasks_to_in_review_logic() -> dict:
    """
    Move all tasks assigned to someone that are in progress to in review.
    """
    email = random.choice(pm_data.project_management_team_emails)
    name = get_first_name(email)

    tasks_in_progress = project_tasks[
        (project_tasks["assigned_to_email"] == email) & (project_tasks["list_name"] == "In Progress")
    ]
    answer = [
        f"""project_management.update_task.func(task_id="{task["task_id"]}", field="list_name", new_value="In Review")"""
        for _, task in tasks_in_progress.iterrows()
    ]
    return {"name": name, "outcome": answer}


def add_new_task_logic() -> dict:
    """
    Add a new task to the backlog and assign it to someone.
    """
    task_dict = get_random_task_dict()
    answer = [
        get_new_task_string(task_dict["task_name"], task_dict["email"], task_dict["board"], task_dict["due_date"])
    ]
    return {"outcome": answer, **task_dict}


def move_overdue_tasks_logic() -> dict:
    """
    Move all overdue tasks that we haven't started on the {board} board to the in-progress
    """
    email = random.choice(pm_data.project_management_team_emails)
    name = get_first_name(email)

    tasks = project_tasks[
        (project_tasks["assigned_to_email"] == email)
        & (project_tasks["list_name"] == "Backlog")
        & (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME.date()))
    ]
    answer = [
        f"""project_management.update_task.func(task_id="{task["task_id"]}", field="list_name", new_value="In Progress")"""
        for _, task in tasks.iterrows()
    ]
    return {"name": name, "outcome": answer}


def move_overdue_in_review_tasks_logic() -> dict:
    """
    Move any of {name}'s tasks that are In Review to Completed
    """
    email = random.choice(pm_data.project_management_team_emails)
    name = get_first_name(email)
    tasks_in_review = project_tasks[
        (project_tasks["assigned_to_email"] == email) & (project_tasks["list_name"] == "In Review")
    ]
    answer = [
        f"""project_management.update_task.func(task_id="{task["task_id"]}", field="list_name", new_value="Completed")"""
        for _, task in tasks_in_review.iterrows()
    ]
    return {"name": name, "outcome": answer}


def reassign_unfinished_tasks_logic() -> dict:
    """
    Reassign all of {name_1}'s in progress tasks to {name_2}
    """
    email_1 = random.choice(pm_data.project_management_team_emails)
    email_2 = random_choice_excluding(pm_data.project_management_team_emails, email_1)
    name_1 = get_first_name(email_1)
    name_2 = get_first_name(email_2)
    tasks_in_progress = project_tasks[
        (project_tasks["assigned_to_email"] == email_1) & (project_tasks["list_name"] == "In Progress")
    ]
    answer = [
        f"""project_management.update_task.func(task_id="{task["task_id"]}", field="assigned_to_email", new_value="{email_2}")"""
        for _, task in tasks_in_progress.iterrows()
    ]
    return {"name_1": name_1, "name_2": name_2, "outcome": answer}


def move_unfinished_tasks_to_backlog_logic() -> dict:
    """
    Move all of {name_1}'s unfinished tasks to the backlog
    """
    email_1 = random.choice(pm_data.project_management_team_emails)
    name_1 = get_first_name(email_1)
    tasks_in_progress = project_tasks[
        (project_tasks["assigned_to_email"] == email_1) & (project_tasks["list_name"] == "In Progress")
    ]
    answer = [
        f"""project_management.update_task.func(task_id="{task["task_id"]}", field="list_name", new_value="Backlog")"""
        for _, task in tasks_in_progress.iterrows()
    ]
    return {"name_1": name_1, "outcome": answer, "email_1": email_1}


def reassign_overdue_tasks_logic() -> dict:
    """
    Give all of {name_1}'s overdue tasks to {name_2}
    """
    email_1 = random.choice(pm_data.project_management_team_emails)
    email_2 = random_choice_excluding(pm_data.project_management_team_emails, email_1)
    name_1 = get_first_name(email_1)
    name_2 = get_first_name(email_2)
    tasks_overdue = project_tasks[
        (project_tasks["assigned_to_email"] == email_1)
        & (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME.date()))
        & (project_tasks["list_name"] == "Backlog")
    ]
    answer = [
        f"""project_management.update_task.func(task_id="{task["task_id"]}", field="assigned_to_email", new_value="{email_2}")"""
        for _, task in tasks_overdue.iterrows()
    ]
    return {"name_1": name_1, "name_2": name_2, "outcome": answer, "email_1": email_1, "email_2": email_2}


def reassign_most_urgent_task_logic() -> dict:
    """
    Take {name_1}'s most urgent task and reassign it to {name_2}
    """
    email_1 = random.choice(pm_data.project_management_team_emails)
    email_2 = random_choice_excluding(pm_data.project_management_team_emails, email_1)
    name_1 = get_first_name(email_1)
    name_2 = get_first_name(email_2)
    tasks = project_tasks[(project_tasks["assigned_to_email"] == email_1) & (project_tasks["list_name"] == "Backlog")]
    most_urgent_task = tasks[tasks["due_date"] == tasks["due_date"].min()]
    # If there are multiple tasks with the same due date, try again
    if (len(most_urgent_task) > 1) or (most_urgent_task.empty):
        return reassign_most_urgent_task_logic()
    task_id = most_urgent_task["task_id"].values[0]
    answer = [
        f"""project_management.update_task.func(task_id="{task_id}", field="assigned_to_email", new_value="{email_2}")"""
    ]
    return {"name_1": name_1, "name_2": name_2, "outcome": answer, "email_1": email_1, "email_2": email_2}


PROJECT_MANAGEMENT_TEMPLATES = [
    {
        "task": "Move all of {name}'s tasks that are in progress to in review",
        "alternative_tasks": [
            "{name} has a bunch of tasks that are in progress. Can you move them to in review?",
            "can you move all of {name}'s tasks that are in progress to in review?",
        ],
        "logic": move_tasks_to_in_review_logic,
    },
    {
        "task": "Add a new task to the {board} backlog called {task_name} and assign it to {name}. It's due on {natural_language_due_date}.",
        "alternative_tasks": [
            "can you add a new task called {task_name} to the {board} backlog and assign it to {name}? It's due on {natural_language_due_date}.",
            "I need to add a new task to the {board} backlog called {task_name} and assign it to {name}. It's due on {natural_language_due_date}. Can you do that?",
        ],
        "logic": add_new_task_logic,
    },
    {
        "task": "Move all of {name}'s overdue tasks in the backlog to in progress",
        "alternative_tasks": [
            "{name} has a bunch of overdue tasks in the backlog. Can you move them to in progress?",
            "can you move all of {name}'s overdue tasks in the backlog to in progress?",
        ],
        "logic": move_overdue_tasks_logic,
    },
    {
        "task": "Move any of {name}'s tasks that are in review to completed",
        "alternative_tasks": [
            "I've finished reviewing all of {name}'s tasks. Can you move all the ones that are in review to completed?",
            "can you move any of {name}'s tasks that are in review to completed?",
        ],
        "logic": move_overdue_in_review_tasks_logic,
    },
    {
        "task": """{name_1} is sick so reassign their in progress tasks to {name_2}.""",
        "alternative_tasks": [
            "can you reassign all of {name_1}'s in progress tasks to {name_2}?",
            "I need to reassign all of {name_1}'s in progress tasks to {name_2}. Can you do that?",
        ],
        "logic": reassign_unfinished_tasks_logic,
    },
    {
        "task": """{name_1} is on vacation now so move all the tasks they are currently working on to the backlog.""",
        "alternative_tasks": [
            "can you move all the tasks {name_1} is currently working on to the backlog?",
            "{name_1} needs a break - move everything they are actively working on to the backlog",
        ],
        "logic": move_unfinished_tasks_to_backlog_logic,
    },
    {
        "task": """Give all the overdue tasks that {name_1} hasn't started to {name_2}.""",
        "alternative_tasks": [
            "{name_2} has some free time so can you give them all of {name_1}'s overdue tasks that they haven't started?",
            "can you give all of {name_1}'s overdue tasks that they haven't started to {name_2}?",
        ],
        "logic": reassign_overdue_tasks_logic,
    },
    {
        "task": """Take {name_1}'s most urgent task and reassign it to {name_2}.""",
        "alternative_tasks": [
            "can you take {name_1}'s most urgent task and reassign it to {name_2}?",
            "I need to take {name_1}'s most urgent task and reassign it to {name_2}. Can you do that?",
        ],
        "logic": reassign_most_urgent_task_logic,
    },
]
for d in PROJECT_MANAGEMENT_TEMPLATES:
    d["domains"] = ["project_management"]


def generate_task_and_outcome() -> None:
    load_data()
    generate_and_write_tasks_and_outcomes(
        PROJECT_MANAGEMENT_TEMPLATES, "data/processed/tasks_and_outcomes/project_management_tasks_and_outcomes.csv"
    )


if __name__ == "__main__":
    generate_task_and_outcome()
