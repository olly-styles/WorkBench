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

def get_random_dict():
    current_customer_name = random.choice(customer_names)
    current_customer_id = CRM_DATA[CRM_DATA["customer_name"] == current_customer_name]["customer_id"].values[0]
    new_customer_name = random.choice(customer_names)
    new_status = random.choice(statuses)
    while new_status == CRM_DATA[CRM_DATA["customer_id"] == current_customer_id]["status"].values[0]:
        new_status = random.choice(statuses)
    new_status_natural_language = new_status.lower()
    assigned_to = random.choice(assigned_tos)
    assigned_to_first_name = assigned_to.split("@")[0].split(".")[0].capitalize()

    return {
        "new_customer_name": new_customer_name,
        "new_status": new_status,
        "new_status_natural_language": new_status_natural_language,
        "current_customer_name": current_customer_name,
        "current_customer_id": current_customer_id,
        "assigned_to": assigned_to,
        "assigned_to_first_name": assigned_to_first_name,
    }


def update_customer_status_logic():
    base_dict = get_random_dict()
    return {
        **base_dict,
        "answer": [
            f"""customer_relationship_manager.update_customer.func(customer_id='{base_dict['current_customer_id']}', field='status', new_value='{base_dict['new_status']}')"""
        ],
    }

def delete_customer_logic():
    base_dict = get_random_dict()
    return {
        **base_dict,
        "answer": [f"""customer_relationship_manager.delete_customer.func(customer_id='{base_dict['current_customer_id']}')"""],
    }
    
def add_lead_logic():
    base_dict = get_random_dict()
    return {
        **base_dict,
        "answer": [
            f"""customer_relationship_manager.add_customer.func(customer_name='{base_dict['new_customer_name']}', assigned_to='{base_dict['assigned_to']}', status='Lead')"""
        ],
    }


CRM_TEMPLATES = [
    {
        "query": "Update the status of {current_customer_name} to {new_status_natural_language} in the crm",
        "logic": update_customer_status_logic,
    },
    {
        "query": "Delete {current_customer_name} from the crm",
        "logic": delete_customer_logic,
    },
    {
        "query": "Add {new_customer_name} as a new lead in the crm and assign them to {assigned_to_first_name}",
        "logic": add_lead_logic,
    },
    {
        "query": "Reassign {customer_name} to {employee_name} in the crm",
        # "logic": reassign_customer_logic,
    },
    {
        "query": "Reassign all of {employee_name}'s leads to {new_employee_name} in the crm",
    },
    {
        "query": "Give {new_employee_name} all of {employee_name}'s leads that we haven't yet made contact with",
    },
    {
        "query": "Give {new_employee_name} all of {employee_name}'s leads that are at least qualified and interested in {product_interest} in the crm",
    },
    {
        "query": "Delete all of {employee_name}'s leads in the crm",
    },
    {
        "query": "Delete all the leads that are interested in {product_interest} in the crm",
    },
    {
        "query": "Delete all the leads that have been dead for {days} days in the crm",
    },
    {
        "query": "Move all customers that haven't responded to a proposal for {weeks} weeks to lost in the crm",
    },
]

# Generate a limited number of unique CRM queries and answers
generated_crm_queries_and_answers = []
max_queries_per_template = 3  # Limit the number of queries per template

if __name__ == "__main__":
    CRM_TEMPLATES = [t for t in CRM_TEMPLATES if "logic" in t]  # fix until we do logic for all templates
    generated_crm_queries_and_answers = generate_all_queries_and_answers(CRM_TEMPLATES, max_queries_per_template)

    df = pd.DataFrame(generated_crm_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/customer_relationship_manager_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
