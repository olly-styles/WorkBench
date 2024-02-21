import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
random.seed(42)

from src.evals.utils import generate_all_queries_and_answers
from src.tools import project_management
from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME
from scripts.data_generation.mocked_data.generate_project_management_data import project_management_team_emails

project_tasks = pd.read_csv("data/processed/project_tasks.csv", dtype=str)
emails = project_tasks["assigned_to"].unique()
task_names = project_tasks["task_name"].unique()
boards = project_tasks["board"].unique()


def move_tasks_to_in_review_logic():
    """
    Move all tasks assigned to someone that are in progress to in review.
    """
    email = random.choice(project_management_team_emails)
    name = email.split("@")[0].split(".")[0]

    tasks_in_progress = project_tasks[
        (project_tasks["assigned_to"] == email) & (project_tasks["list_name"] == "In Progress")
    ]
    answer = []
    for _, task in tasks_in_progress.iterrows():
        task_id = task["task_id"]
        answer.append(
            f"""project_management.update_task.func(task_id='{task_id}', field='list_name', new_value='In Review')"""
        )
    return {"name": name, "answer": answer}


def add_new_task_logic():
    """
    Add a new task to the backlog and assign it to someone.
    """
    email = random.choice(project_management_team_emails)
    name = email.split("@")[0].split(".")[0]
    task_name = random.choice(task_names)
    board = random.choice(boards)
    due_date = HARDCODED_CURRENT_TIME.date() + pd.Timedelta(days=random.randint(1, 7))
    answer = [
        f"""project_management.create_task.func(task_name='{task_name}', board='{board}', assigned_to='{email}', due_date='{due_date}', list_name='Backlog')"""
    ]
    return {"task_name": task_name, "board": board, "assigned_to": name, "due_date": due_date, "answer": answer}


def move_overdue_tasks_logic():
    """
    Move all overdue tasks that we haven't started on the {board} board to the in-progress
    """
    email = random.choice(project_management_team_emails)
    name = email.split("@")[0].split(".")[0]

    tasks = project_tasks[
        (project_tasks["assigned_to"] == email)
        & (project_tasks["list_name"] == "Backlog")
        & (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME))
    ]
    answer = []
    for _, task in tasks.iterrows():
        task_id = task["task_id"]
        answer.append(
            f"""project_management.update_task.func(task_id='{task_id}', field='list_name', new_value='In Progress')"""
        )
    return {"name": name, "answer": answer}


def move_tasks_to_backlog_and_delete_completed_logic():
    """
    Move all In Progress tasks on the {board} board back to the Backlog and delete any tasks in the Completed list
    """
    board = random.choice(boards)
    tasks_in_progress = project_tasks[(project_tasks["board"] == board) & (project_tasks["list_name"] == "In Progress")]
    tasks_completed = project_tasks[(project_tasks["board"] == board) & (project_tasks["list_name"] == "Completed")]
    answer = []
    for _, task in tasks_in_progress.iterrows():
        task_id = task["task_id"]
        answer.append(
            f"""project_management.update_task.func(task_id='{task_id}', field='list_name', new_value='Backlog')"""
        )
    return {"board": board, "answer": answer}


def move_overdue_in_review_tasks_logic():
    """
    Move any of {name}'s tasks that are In Review to Completed
    """
    email = random.choice(project_management_team_emails)
    name = email.split("@")[0].split(".")[0]
    tasks_in_review = project_tasks[
        (project_tasks["assigned_to"] == email) & (project_tasks["list_name"] == "In Review")
    ]
    answer = []
    for _, task in tasks_in_review.iterrows():
        task_id = task["task_id"]
        answer.append(
            f"""project_management.update_task.func(task_id='{task_id}', field='list_name', new_value='Completed')"""
        )
    return {"name": name, "answer": answer}


PROJECT_MANAGEMENT_TEMPLATES = [
    {
        "query": "Move all of {name}'s tasks that are in progress to in review",
        "logic": move_tasks_to_in_review_logic,
    },
    {
        "query": "Add a new task to the {board} backlog called {task_name} and assign it to {assigned_to}. It's due on {due_date}.",
        "logic": add_new_task_logic,
    },
    {
        "query": "Move all of {name}'s overdue tasks in the backlog to in progress",
        "logic": move_overdue_tasks_logic,
    },
    {
        "query": "We've finished our {board} sprint. Can you move all in progress tasks on the {board} board back to the backlog?",
        "logic": move_tasks_to_backlog_and_delete_completed_logic,
    },
    {
        "query": "Move any of {name}'s tasks that are in review to completed",
        "logic": move_overdue_in_review_tasks_logic,
    },
]

max_queries_per_template = 1  # Limit the number of queries per template

if __name__ == "__main__":
    generated_queries_and_answers = generate_all_queries_and_answers(
        PROJECT_MANAGEMENT_TEMPLATES, max_queries_per_template
    )
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/project_management_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
