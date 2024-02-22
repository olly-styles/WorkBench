import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import generate_all_queries_and_answers
from scripts.data_generation.mocked_data.generate_customer_relationship_manager_data import generate_random_name

random.seed(42)

CRM_DATA = pd.read_csv("data/processed/customer_relationship_manager_data.csv", dtype=str)
customer_names = list(CRM_DATA["customer_name"].unique())
customer_emails = list(CRM_DATA["customer_email"].unique())
product_interests = list(CRM_DATA["product_interest"].unique())
statuses = ["Qualified", "Won", "Lost", "Lead", "Proposal"]
assigned_tos = list(CRM_DATA["assigned_to"].unique())
customer_ids = list(CRM_DATA["customer_id"].unique())


def generate_new_customer_name():
    first_names = ["David", "James", "Robert", "William", "Mary", "Patricia", "Linda"]
    last_names = ["Jones", "Miller", "Davis", "Garcia", "Martinez", "Robinson", "Mehta"]
    return generate_random_name(first_names, last_names)


def update_customer_status_logic():
    customer_name = random.choice(customer_names)
    customer_id = CRM_DATA[CRM_DATA["customer_name"] == customer_name]["customer_id"].values[0]
    new_status = random.choice(statuses).lower()
    while new_status == CRM_DATA[CRM_DATA["customer_id"] == customer_id]["status"].values[0]:
        new_status = random.choice(statuses)
    return {
        "customer_name": customer_name,
        "new_status": new_status,
        "answer": [
            f"""customer_relationship_manager.update_customer.func(customer_id='{customer_id}', field='status', new_value='{new_status}')"""
        ],
    }


def delete_customer_logic():
    customer_name = random.choice(customer_names)
    customer_id = CRM_DATA[CRM_DATA["customer_name"] == customer_name]["customer_id"].values[0]
    return {
        "customer_name": customer_name,
        "answer": [f"""customer_relationship_manager.delete_customer.func(customer_id='{customer_id}')"""],
    }


def add_lead_logic():
    customer_name = generate_new_customer_name()
    assigned_to = random.choice(assigned_tos)
    assigned_to_first_name = assigned_to.split("@")[0].split(".")[0].capitalize()
    return {
        "customer_name": customer_name,
        "assigned_to_first_name": assigned_to_first_name,
        "answer": [
            f"""customer_relationship_manager.add_customer.func(customer_name='{customer_name}', assigned_to='{assigned_to}', status='Lead')"""
        ],
    }


CRM_TEMPLATES = [
    {
        "query": "Update the status of {customer_name} to {new_status} in the crm",
        "logic": update_customer_status_logic,
    },
    {
        "query": "Delete {customer_name} from the crm",
        "logic": delete_customer_logic,
    },
    {
        "query": "Add {customer_name} as a new lead in the crm and assign them to {assigned_to_first_name}",
        "logic": add_lead_logic,
    },
]

# Generate a limited number of unique CRM queries and answers
generated_crm_queries_and_answers = []
max_queries_per_template = 3  # Limit the number of queries per template

if __name__ == "__main__":
    generated_crm_queries_and_answers = generate_all_queries_and_answers(CRM_TEMPLATES, max_queries_per_template)

    df = pd.DataFrame(generated_crm_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/customer_relationship_manager_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
