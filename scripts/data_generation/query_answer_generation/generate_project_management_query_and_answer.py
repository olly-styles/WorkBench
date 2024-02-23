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
from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME, get_natural_language_date
from scripts.data_generation.mocked_data.generate_project_management_data import project_management_team_emails

project_tasks = pd.read_csv("data/processed/project_tasks.csv", dtype=str)
emails = project_tasks["assigned_to"].unique()
task_names = project_tasks["task_name"].unique()
boards = project_tasks["board"].unique()


def get_random_task_dict():
    task = random.choice(task_names)
    email = random.choice(emails)
    board = random.choice(boards)
    due_date = HARDCODED_CURRENT_TIME.date() + pd.Timedelta(days=random.randint(1, 7))
    natural_language_due_date = get_natural_language_date(due_date)
    return {
        "task_name": task,
        "email": email,
        "board": board,
        "due_date": due_date,
        "natural_language_due_date": natural_language_due_date,
        "name": email.split("@")[0].split(".")[0],
    }

def get_new_task_string(task_name, email, board, due_date):
    return f"""project_management.create_task.func(task_name='{task_name}', board='{board}', assigned_to='{email}', due_date='{due_date}', list_name='Backlog')"""

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
    task_dict = get_random_task_dict()
    answer = [get_new_task_string(task_dict["task_name"], task_dict["email"], task_dict["board"], task_dict["due_date"])]
    return {"answer": answer, **task_dict}

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
        "query": "Add a new task to the {board} backlog called {task_name} and assign it to {name}. It's due on {natural_language_due_date}.",
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
    {
        "query": """{name_1} is sick so reassign their unfinished tasks to {name_2}."""
    },
    {
        "query": """{name_1} is on vacation now so move all their unfinished tasks to the backlog."""
    },
    {
        "query": """{name_1} is sick, so move any tasks they haven't started to the backlog and anything in progress to the person with the fewest unfinished tasks."""
    },
    {
        "query" """Give all of {name_1}'s overdue tasks to {name_2}."""
    },
    {
        "query": """On {board}, make a backlog task on called {task_name} and assign it to the person with the fewest {in_progress_or_backlog} tasks. It's due on {day_of_week}.""",
    },
    {
        "query": """Take {name_1}'s most urgent task and reassign it to {name_2}."""
    },
    {
        "query": """Reassign {name_1}'s most urgent task to {name_2} - give them a deadline of {days} days after their final {in_progress_or_backlog} task."""
    },
    {
        "query": """If {name} has more than {threshold} backlog tasks, assign the most urgent one to the person with the fewest {in_progress_or_backlog} tasks.""",
    },
    {
        "query": """If {name} has finished their tasks, give them one called {task_name}. It's due on {day_of_week}.""",
    },
    {
        "query": """If {name} hasn't got any overdue tasks, make one for them called {task_name}. It's due tomorrow.""",
    }
]

max_queries_per_template = 1  # Limit the number of queries per template

if __name__ == "__main__":
    PROJECT_MANAGEMENT_TEMPLATES = [t for t in PROJECT_MANAGEMENT_TEMPLATES if "logic" in t]
    generated_queries_and_answers = generate_all_queries_and_answers(
        PROJECT_MANAGEMENT_TEMPLATES, max_queries_per_template
    )
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/project_management_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
