import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME

SEED_DATA_DIR = Path(__file__).parent.parent / "seed_data"
PM_SEED = json.loads((SEED_DATA_DIR / "project_management.json").read_text())

team_member_emails: Any = None
team_with_no_overdue_tasks: Any = None
backend_team_emails: Any = None
frontend_team_emails: Any = None
design_team_emails: Any = None
project_management_team_emails: Any = None
sales_team_emails: Any = None


def load_team_emails() -> None:
    global team_member_emails, team_with_no_overdue_tasks
    global backend_team_emails, frontend_team_emails, design_team_emails
    global project_management_team_emails, sales_team_emails

    if team_member_emails is not None:
        return

    team_member_emails = pd.read_csv("data/raw/email_addresses.csv", header=None).values.flatten()
    team_with_no_overdue_tasks = team_member_emails[: int(len(team_member_emails) / 3)]
    num_teams = 4
    backend_team_emails = team_member_emails[: len(team_member_emails) // num_teams]
    frontend_team_emails = team_member_emails[
        len(team_member_emails) // num_teams : 2 * len(team_member_emails) // num_teams
    ]
    design_team_emails = team_member_emails[
        2 * len(team_member_emails) // num_teams : 3 * len(team_member_emails) // num_teams
    ]
    project_management_team_emails = list(backend_team_emails) + list(frontend_team_emails) + list(design_team_emails)
    sales_team_emails = team_member_emails[3 * len(team_member_emails) // num_teams :]


task_templates = {
    "Back end": [
        "Implement {feature} API",
        "Fix bug in {module} module",
        "Optimize database query for {functionality}",
        "Add authentication for {service}",
        "Update {library_framework} to latest version",
    ],
    "Front end": [
        "Design UI for {page_feature}",
        "Implement responsive layout for {page_feature}",
        "Integrate {API_service} with frontend",
        "Fix alignment issue in {page_feature}",
        "Add animation to {element}",
    ],
    "Design": [
        "Create wireframe for {page_feature}",
        "Update brand colors in {product_section}",
        "Design logo for {product_section}",
        "Improve UX of {workflow_process}",
        "Develop prototype for {feature}",
    ],
}


# Define a function to generate random dates for task due dates
def generate_random_due_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def choose_list(
    lists: list[str],
    probability_list_1: float = 0.7,
    probability_list_2: float = 0.04,
    probability_list_3: float = 0.16,
    probability_list_4: float = 0.1,
) -> str:
    return np.random.choice(lists, p=[probability_list_1, probability_list_2, probability_list_3, probability_list_4])


# Function to generate a random task
def create_task(
    project_management_data: pd.DataFrame,
    task_templates: dict[str, list[str]],
    team_emails_by_board: dict[str, Any],
    lists: list[str],
    start_date: date,
    end_date: date,
    board: str,
) -> tuple[str, str, str, str, date, str]:
    template = random.choice(task_templates[board])
    # Selecting the appropriate team member emails based on the board
    team_member_emails = team_emails_by_board[board]

    # Choose a unique task-person combination
    while True:
        assigned_to_email = random.choice(team_member_emails)
        task_name = template.format(
            feature=random.choice(PM_SEED["features"]),
            module=random.choice(PM_SEED["modules"]),
            functionality=random.choice(PM_SEED["functionalities"]),
            service=random.choice(PM_SEED["services"]),
            library_framework=random.choice(PM_SEED["library_frameworks"]),
            page_feature=random.choice(PM_SEED["page_features"]),
            API_service=random.choice(PM_SEED["api_services"]),
            element=random.choice(PM_SEED["elements"]),
            product_section=random.choice(PM_SEED["product_sections"]),
            workflow_process=random.choice(PM_SEED["workflow_processes"]),
        )
        # If this person has not been assigned this task, break the loop
        if not (
            (project_management_data["task_name"] == task_name)
            & (project_management_data["assigned_to_email"] == assigned_to_email)
        ).any():
            break

    due_date = generate_random_due_date(start_date, end_date)
    task_id = str(len(project_management_data)).zfill(8)
    list_name = choose_list(lists)
    if due_date < HARDCODED_CURRENT_TIME.date() and assigned_to_email in team_with_no_overdue_tasks:
        list_name = "Completed"
    return task_id, task_name, assigned_to_email, list_name, due_date, board


# Sample data for tasks, team members, and lists


def generate_data() -> None:
    load_team_emails()
    np.random.seed(42)
    random.seed(42)

    lists = ["Backlog", "In Progress", "In Review", "Completed"]
    boards = ["Back end", "Front end", "Design"]

    # Setting up the project board
    project_management_data = pd.DataFrame(
        columns=pd.Index(["task_id", "task_name", "assigned_to_email", "list_name", "due_date", "board"])
    )

    # Simulate task generation
    start_date = HARDCODED_CURRENT_TIME.date() - timedelta(days=3)  # Some tasks are overdue
    end_date = HARDCODED_CURRENT_TIME.date() + timedelta(days=13)  # All tasks are due within 14 days

    # Dictionary of team member emails by board
    team_emails_by_board = {
        "Back end": backend_team_emails,
        "Front end": frontend_team_emails,
        "Design": design_team_emails,
    }
    for board in tqdm(boards):
        for _ in range(100):
            task = create_task(
                project_management_data.copy(), task_templates, team_emails_by_board, lists, start_date, end_date, board
            )
            project_management_data.loc[len(project_management_data)] = task

    # Optional: Sort by due date or any other column as needed
    project_management_data = project_management_data.sort_values(by="due_date").reset_index(drop=True)

    # Save to CSV
    project_management_data.to_csv("data/processed/project_tasks.csv", index=False)


if __name__ == "__main__":
    generate_data()
