import random
from datetime import timedelta
from typing import Any

import pandas as pd

from src.data_generation.data_generation_utils import (
    HARDCODED_CURRENT_TIME,
    generate_and_write_tasks_and_outcomes,
    get_first_name,
    random_choice_excluding,
)

CRM_DATA: Any = None
customer_names: Any = None
product_interests: Any = None
statuses = ["Qualified", "Won", "Lost", "Lead", "Proposal"]
assigned_to_emails: Any = None


def load_data() -> None:
    global CRM_DATA, customer_names, product_interests, assigned_to_emails
    if CRM_DATA is not None:
        return
    CRM_DATA = pd.read_csv("data/processed/customer_relationship_manager_data.csv", dtype=str)
    customer_names = list(CRM_DATA["customer_name"].unique())
    product_interests = list(CRM_DATA["product_interest"].unique())
    assigned_to_emails = list(CRM_DATA["assigned_to_email"].unique())


def get_random_dict() -> dict:
    current_customer_name = random.choice(customer_names)
    current_customer_id = CRM_DATA[CRM_DATA["customer_name"] == current_customer_name]["customer_id"].values[0]
    new_customer_name = random.choice(customer_names)
    current_status = CRM_DATA[CRM_DATA["customer_id"] == current_customer_id]["status"].values[0]
    new_status = random_choice_excluding(statuses, current_status)
    new_status_natural_language = new_status.lower()
    assigned_to_email = random.choice(assigned_to_emails)
    assigned_to_first_name = get_first_name(assigned_to_email).capitalize()
    new_assigned_to_email = random_choice_excluding(assigned_to_emails, assigned_to_email)
    new_assigned_to_first_name = get_first_name(new_assigned_to_email).capitalize()
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


def update_customer_status_logic() -> dict:
    base_dict = get_random_dict()
    return {
        **base_dict,
        "outcome": [
            f"""customer_relationship_manager.update_customer.func(customer_id="{base_dict["current_customer_id"]}", field="status", new_value="{base_dict["new_status"]}")"""
        ],
    }


def delete_customer_logic() -> dict:
    base_dict = get_random_dict()
    return {
        **base_dict,
        "outcome": [
            f"""customer_relationship_manager.delete_customer.func(customer_id="{base_dict["current_customer_id"]}")"""
        ],
    }


def add_lead_logic() -> dict:
    base_dict = get_random_dict()
    return {
        **base_dict,
        "outcome": [
            f"""customer_relationship_manager.add_customer.func(customer_name="{base_dict["new_customer_name"]}", assigned_to_email="{base_dict["assigned_to_email"]}", status="Lead")"""
        ],
    }


def reassign_customer_logic() -> dict:
    base_dict = get_random_dict()
    return {
        **base_dict,
        "outcome": [
            f"""customer_relationship_manager.update_customer.func(customer_id="{base_dict["current_customer_id"]}", field="assigned_to_email", new_value="{base_dict["assigned_to_email"]}")"""
        ],
    }


def reassign_all_leads_for_product_logic() -> dict:
    base_dict = get_random_dict()
    employee_leads = CRM_DATA[
        (CRM_DATA["assigned_to_email"] == base_dict["assigned_to_email"])
        & (CRM_DATA["status"] == "Lead")
        & (CRM_DATA["product_interest"] == base_dict["product_interest"])
    ]
    answer = [
        f"""customer_relationship_manager.update_customer.func(customer_id="{row["customer_id"]}", field="assigned_to_email", new_value="{base_dict["new_assigned_to_email"]}")"""
        for _, row in employee_leads.iterrows()
    ]
    return {
        **base_dict,
        "outcome": answer,
    }


def reassign_all_qualified_leads_for_product_logic() -> dict:
    base_dict = get_random_dict()
    employee_leads = CRM_DATA[
        (CRM_DATA["assigned_to_email"] == base_dict["assigned_to_email"])
        & (CRM_DATA["status"].isin(["Qualified", "Proposal"]))
        & (CRM_DATA["product_interest"] == base_dict["product_interest"])
    ]
    answer = [
        f"""customer_relationship_manager.update_customer.func(customer_id="{row["customer_id"]}", field="assigned_to_email", new_value="{base_dict["new_assigned_to_email"]}")"""
        for _, row in employee_leads.iterrows()
    ]
    return {
        **base_dict,
        "outcome": answer,
    }


def delete_all_customers_in_stage_logic() -> dict:
    base_dict = get_random_dict()
    customers_to_delete = CRM_DATA[
        (CRM_DATA["assigned_to_email"] == base_dict["assigned_to_email"])
        & (CRM_DATA["status"] == base_dict["new_status"])
        & (CRM_DATA["product_interest"] == base_dict["product_interest"])
    ]
    answer = [
        f"""customer_relationship_manager.delete_customer.func(customer_id="{row["customer_id"]}")"""
        for _, row in customers_to_delete.iterrows()
    ]
    return {
        **base_dict,
        "outcome": answer,
    }


def move_unresponsive_customers_to_lost_logic() -> dict:
    base_dict = get_random_dict()
    weeks = random.randint(3, 6)
    customers_to_move = CRM_DATA[
        (CRM_DATA["status"] == "Proposal")
        & (CRM_DATA["last_contact_date"] < str(HARDCODED_CURRENT_TIME - timedelta(weeks=weeks)))
        & (CRM_DATA["product_interest"] == base_dict["product_interest"])
    ]
    answer = [
        f"""customer_relationship_manager.update_customer.func(customer_id="{row["customer_id"]}", field="status", new_value="Lost")"""
        for _, row in customers_to_move.iterrows()
    ]
    return {
        **base_dict,
        "weeks": weeks,
        "outcome": answer,
    }


CRM_TEMPLATES = [
    {
        "task": "Update the status of {current_customer_name} to {new_status_natural_language} in the crm",
        "alternative_tasks": [
            "{current_customer_name} has moved to {new_status_natural_language} status. Can you update that in the crm?",
            "We've got a new customer that's moved to {new_status_natural_language} status. Can you update {current_customer_name} to {new_status_natural_language} in the crm?",
        ],
        "logic": update_customer_status_logic,
    },
    {
        "task": "Delete {current_customer_name} from the crm",
        "alternative_tasks": [
            "We no longer need to keep {current_customer_name} in the crm. Can you delete them?",
            "{current_customer_name} is no longer a customer. Can you delete them from the crm?",
        ],
        "logic": delete_customer_logic,
    },
    {
        "task": "Add {new_customer_name} as a new lead in the crm and assign them to {assigned_to_first_name}",
        "alternative_tasks": [
            "We've got a new lead called {new_customer_name}. Can you add them to the crm and assign them to {assigned_to_first_name}?",
            "can you add {new_customer_name} to the crm? They're a new lead and need to be assigned to {assigned_to_first_name}",
        ],
        "logic": add_lead_logic,
    },
    {
        "task": "Reassign {current_customer_name} to {assigned_to_first_name} in the crm",
        "alternative_tasks": [
            "{assigned_to_first_name} is taking over {current_customer_name}. Can you reassign them in the crm?",
            "We're moving {current_customer_name} to {assigned_to_first_name}. Can you make that change in the crm?",
        ],
        "logic": reassign_customer_logic,
    },
    {
        "task": "Reassign all of {assigned_to_first_name}'s leads that are interested in {natural_language_product_interest} to {new_assigned_to_first_name} in the crm.",
        "alternative_tasks": [
            "We're moving all of {assigned_to_first_name}'s leads that are interested in {natural_language_product_interest} to {new_assigned_to_first_name}. Can you make that change in the crm?",
            "{new_assigned_to_first_name} is taking over all of {assigned_to_first_name}'s leads that are interested in {natural_language_product_interest}. Can you reassign them in the crm?",
        ],
        "logic": reassign_all_leads_for_product_logic,
    },
    {
        "task": "Give {new_assigned_to_first_name} all of {assigned_to_first_name}'s customers that are interested in {natural_language_product_interest} and are either qualified or in proposal in the crm",
        "alternative_tasks": [
            "{new_assigned_to_first_name} is taking over all of {assigned_to_first_name}'s customers that are interested in {natural_language_product_interest} and are either qualified or in proposal. Can you reassign them in the crm?",
            "I need to move all of {assigned_to_first_name}'s customers that are interested in {natural_language_product_interest} and are either qualified or in proposal to {new_assigned_to_first_name}. Can you make that change in the crm?",
        ],
        "logic": reassign_all_qualified_leads_for_product_logic,
    },
    {
        "task": "Delete all of {assigned_to_first_name}'s customers that are in the {new_status_natural_language} stage and interested in {natural_language_product_interest} in the crm",
        "alternative_tasks": [
            "We no longer need to keep all of {assigned_to_first_name}'s customers that are in the {new_status_natural_language} stage and interested in {natural_language_product_interest}. Can you delete them from the crm?",
            "I need to remove all of {assigned_to_first_name}'s customers that are in the {new_status_natural_language} stage and interested in {natural_language_product_interest} from the crm. Can you make that change?",
        ],
        "logic": delete_all_customers_in_stage_logic,
    },
    {
        "task": "Move all customers that haven't responded to a proposal for the {natural_language_product_interest} product in {weeks} weeks to lost in the crm",
        "alternative_tasks": [
            "I think there's a few customers that haven't responded to a proposal for the {natural_language_product_interest} product in {weeks} weeks. Can you move them to lost in the crm?",
            "We need to move all customers that haven't responded to a proposal for the {natural_language_product_interest} product in {weeks} weeks to lost. Can you update the CRM?",
        ],
        "logic": move_unresponsive_customers_to_lost_logic,
    },
]
for d in CRM_TEMPLATES:
    d["domains"] = ["customer_relationship_manager"]


def generate_task_and_outcome() -> None:
    load_data()
    generate_and_write_tasks_and_outcomes(
        CRM_TEMPLATES, "data/processed/tasks_and_outcomes/customer_relationship_manager_tasks_and_outcomes.csv"
    )


if __name__ == "__main__":
    generate_task_and_outcome()
