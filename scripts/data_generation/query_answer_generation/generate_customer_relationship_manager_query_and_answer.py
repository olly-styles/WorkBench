from datetime import timedelta
import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import generate_all_queries_and_answers
from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME
from scripts.data_generation.mocked_data.generate_customer_relationship_manager_data import generate_random_name

random.seed(42)

CRM_DATA = pd.read_csv("data/processed/customer_relationship_manager_data.csv", dtype=str)
customer_names = list(CRM_DATA["customer_name"].unique())
customer_emails = list(CRM_DATA["customer_email"].unique())
product_interests = list(CRM_DATA["product_interest"].unique())
statuses = ["Qualified", "Won", "Lost", "Lead", "Proposal"]
assigned_to_emails = list(CRM_DATA["assigned_to_email"].unique())
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
    assigned_to_email = random.choice(assigned_to_emails)
    assigned_to_first_name = assigned_to_email.split("@")[0].split(".")[0].capitalize()
    new_assigned_to_email = random.choice(assigned_to_emails)
    while new_assigned_to_email == assigned_to_email:
        new_assigned_to_email = random.choice(assigned_to_emails)
    new_assigned_to_first_name = new_assigned_to_email.split("@")[0].split(".")[0].capitalize()
    product_interest = random.choice(product_interests)
    natural_language_product_interest = product_interest.lower()

    return {
        "new_customer_name": new_customer_name,
        "new_status": new_status,
        "new_status_natural_language": new_status_natural_language,
        "current_customer_name": current_customer_name,
        "current_customer_id": current_customer_id,
        "assigned_to_email": assigned_to_email,
        "assigned_to_first_name": assigned_to_first_name,
        "new_assigned_to_email": new_assigned_to_email,
        "new_assigned_to_first_name": new_assigned_to_first_name,
        "product_interest": product_interest,
        "natural_language_product_interest": natural_language_product_interest,
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
        "answer": [
            f"""customer_relationship_manager.delete_customer.func(customer_id='{base_dict['current_customer_id']}')"""
        ],
    }


def add_lead_logic():
    base_dict = get_random_dict()
    return {
        **base_dict,
        "answer": [
            f"""customer_relationship_manager.add_customer.func(customer_name='{base_dict['new_customer_name']}', assigned_to_email='{base_dict['assigned_to_email']}', status='Lead')"""
        ],
    }


def reassign_customer_logic():
    base_dict = get_random_dict()
    return {
        **base_dict,
        "answer": [
            f"""customer_relationship_manager.update_customer.func(customer_id='{base_dict['current_customer_id']}', field='assigned_to_email', new_value='{base_dict['assigned_to_email']}')"""
        ],
    }


def reassign_all_leads_for_product_logic():
    base_dict = get_random_dict()
    employee_leads = CRM_DATA[
        (CRM_DATA["assigned_to_email"] == base_dict["assigned_to_email"])
        & (CRM_DATA["status"] == "Lead")
        & (CRM_DATA["product_interest"] == base_dict["product_interest"])
    ]
    answer = []
    for _, row in employee_leads.iterrows():
        answer.append(
            f"""customer_relationship_manager.update_customer.func(customer_id='{row['customer_id']}', field='assigned_to_email', new_value='{base_dict['new_assigned_to_email']}')"""
        )
    return {
        **base_dict,
        "answer": answer,
    }


def reassign_all_qualified_leads_for_product_logic():
    base_dict = get_random_dict()
    employee_leads = CRM_DATA[
        (CRM_DATA["assigned_to_email"] == base_dict["assigned_to_email"])
        & (CRM_DATA["status"].isin(["Qualified", "Proposal", "Won"]))
        & (CRM_DATA["product_interest"] == base_dict["product_interest"])
    ]
    answer = []
    for _, row in employee_leads.iterrows():
        answer.append(
            f"""customer_relationship_manager.update_customer.func(customer_id='{row['customer_id']}', field='assigned_to_email', new_value='{base_dict['new_assigned_to_email']}')"""
        )
    return {
        **base_dict,
        "answer": answer,
    }


def delete_all_customers_in_stage_logic():
    base_dict = get_random_dict()
    customers_to_delete = CRM_DATA[
        (CRM_DATA["assigned_to_email"] == base_dict["assigned_to_email"])
        & (CRM_DATA["status"] == base_dict["new_status"])
        & (CRM_DATA["product_interest"] == base_dict["product_interest"])
    ]
    answer = []
    for _, row in customers_to_delete.iterrows():
        answer.append(f"""customer_relationship_manager.delete_customer.func(customer_id='{row['customer_id']}')""")
    return {
        **base_dict,
        "answer": answer,
    }


def move_unresponsive_customers_to_lost_logic():
    base_dict = get_random_dict()
    weeks = random.randint(3, 6)
    customers_to_move = CRM_DATA[
        (CRM_DATA["status"] == "Proposal")
        & (CRM_DATA["last_contact_date"] < str(HARDCODED_CURRENT_TIME - timedelta(weeks=weeks)))
        & (CRM_DATA["product_interest"] == base_dict["product_interest"])
    ]
    answer = []
    for _, row in customers_to_move.iterrows():
        answer.append(
            f"""customer_relationship_manager.update_customer.func(customer_id='{row['customer_id']}', field='status', new_value='Lost')"""
        )
    return {
        **base_dict,
        "weeks": weeks,
        "answer": answer,
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
        "query": "Reassign {current_customer_name} to {assigned_to_first_name} in the crm",
        "logic": reassign_customer_logic,
    },
    {
        "query": "Reassign all of {assigned_to_first_name}'s leads that are interested in {natural_language_product_interest} to {assigned_to_first_name} in the crm.",
        "logic": reassign_all_leads_for_product_logic,
    },
    {
        "query": "Give {new_assigned_to_first_name} all of {assigned_to_first_name}'s customers that are interested in {natural_language_product_interest} and are either qualified or in proposal in the crm",
        "logic": reassign_all_qualified_leads_for_product_logic,
    },
    {
        "query": "Delete all of {assigned_to_first_name}'s customers that are in the {new_status_natural_language} stage and interested in {natural_language_product_interest} in the crm",
        "logic": delete_all_customers_in_stage_logic,
    },
    {
        "query": "Move all customers that haven't responded to a proposal for the {natural_language_product_interest} product in {weeks} weeks to lost in the crm",
        "logic": move_unresponsive_customers_to_lost_logic,
    },
]
for d in CRM_TEMPLATES:
    d["domains"] = ["customer_relationship_manager"]

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
