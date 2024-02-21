import pandas as pd
import numpy as np
import random
from datetime import timedelta
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
random.seed(42)

from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME


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
def generate_random_due_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))


def choose_list(lists, probability_list_1=0.7, probability_list_2=0.04, probability_list_3=0.16, probability_list_4=0.1):
    list_name = np.random.choice(lists, p=[probability_list_1, probability_list_2, probability_list_3, probability_list_4])
    return list_name


# Function to generate a random task
def create_task(task_templates, team_emails_by_board, lists, start_date, end_date, board):
    template = random.choice(task_templates[board])
    # Selecting the appropriate team member emails based on the board
    team_member_emails = team_emails_by_board[board]

    # Choose a unique task-person combination
    while True:
        assigned_to = random.choice(team_member_emails)
        task_name = template.format(
            feature=random.choice(
                [
                    "login system",
                    "payment gateway",
                    "user profile management",
                    "search functionality",
                    "data export",
                    "report generation",
                ]
            ),
            module=random.choice(
                ["user authentication", "payment processing", "content delivery", "data storage", "user management"]
            ),
            functionality=random.choice(
                ["search functionality", "data export", "report generation", "user management", "content delivery"]
            ),
            service=random.choice(
                ["email notification", "third-party login", "cloud storage", "payment gateway", "file upload"]
            ),
            library_framework=random.choice(["react", "Django", "Node.js", "Flask", "Vue.js"]),
            page_feature=random.choice(["homepage", "dashboard", "settings page", "profile page", "landing page"]),
            API_service=random.choice(
                ["REST API", "Google Maps API", "Stripe payment API", "Twilio SMS API", "AWS S3 API"]
            ),
            element=random.choice(
                ["navigation bar", "modal window", "form submission button", "dropdown menu", "carousel"]
            ),
            product_section=random.choice(["mobile app", "website", "admin panel", "e-commerce platform", "blog"]),
            workflow_process=random.choice(
                ["checkout process", "sign-up flow", "feedback submission", "onboarding process", "content creation"]
            ),
        )
        # If this person has not been assigned this task, break the loop
        if not (
            (project_management_data["task_name"] == task_name)
            & (project_management_data["assigned_to"] == assigned_to)
        ).any():
            break

    list_name = choose_list(lists)
    due_date = generate_random_due_date(start_date, end_date)
    task_id = str(len(project_management_data)).zfill(8)
    return task_id, task_name, assigned_to, list_name, due_date, board


# Sample data for tasks, team members, and lists
team_member_emails = pd.read_csv("data/raw/email_addresses.csv", header=None).values.flatten()

num_teams = 4
backend_team_emails = team_member_emails[: len(team_member_emails) // num_teams]
frontend_team_emails = team_member_emails[len(team_member_emails) // num_teams : 2 * len(team_member_emails) // num_teams]
design_team_emails = team_member_emails[2 * len(team_member_emails) // num_teams : 3 * len(team_member_emails) // num_teams]
project_management_team_emails = backend_team_emails + frontend_team_emails + design_team_emails
sales_team_emails = team_member_emails[3 * len(team_member_emails) // num_teams :]

lists = ["Backlog", "In Progress", "In Review", "Completed"]
boards = ["Back end", "Front end", "Design"]

# Setting up the project board
project_management_data = pd.DataFrame(
    columns=["task_id", "task_name", "assigned_to", "list_name", "due_date", "board"]
)

# Simulate task generation
start_date = HARDCODED_CURRENT_TIME.date() - timedelta(days=2)  # Some tasks are overdue
end_date = HARDCODED_CURRENT_TIME.date() + timedelta(days=14)  # All tasks are due within 14 days

# Dictionary of team member emails by board
team_emails_by_board = {
    "Back end": backend_team_emails,
    "Front end": frontend_team_emails,
    "Design": design_team_emails,
}

if __name__ == "__main__":
    # Adjusted task generation loop
    for board in boards:
        for i in range(100):
            task = create_task(task_templates, team_emails_by_board, lists, start_date, end_date, board)
            project_management_data.loc[len(project_management_data)] = task

    # Optional: Sort by due date or any other column as needed
    project_management_data = project_management_data.sort_values(by="due_date").reset_index(drop=True)

    # Save to CSV
    project_management_data.to_csv("data/processed/project_tasks.csv", index=False)

    print("Mocked project management data generated successfully.")
