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
            f"""customer_relationship_manager.update_customer.func(customer_id="{base_dict['current_customer_id']}", field="status", new_value="{base_dict['new_status']}")"""
        ],
    }


def delete_customer_logic():
    base_dict = get_random_dict()
    return {
        **base_dict,
        "answer": [
            f"""customer_relationship_manager.delete_customer.func(customer_id="{base_dict['current_customer_id']}")"""
        ],
    }


def add_lead_logic():
    base_dict = get_random_dict()
    return {
        **base_dict,
        "answer": [
            f"""customer_relationship_manager.add_customer.func(customer_name="{base_dict['new_customer_name']}", assigned_to_email="{base_dict['assigned_to_email']}", status="Lead")"""
        ],
    }


def reassign_customer_logic():
    base_dict = get_random_dict()
    return {
        **base_dict,
        "answer": [
            f"""customer_relationship_manager.update_customer.func(customer_id="{base_dict['current_customer_id']}", field="assigned_to_email", new_value="{base_dict['assigned_to_email']}")"""
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
            f"""customer_relationship_manager.update_customer.func(customer_id="{row['customer_id']}", field="assigned_to_email", new_value="{base_dict['new_assigned_to_email']}")"""
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
            f"""customer_relationship_manager.update_customer.func(customer_id="{row['customer_id']}", field="assigned_to_email", new_value="{base_dict['new_assigned_to_email']}")"""
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
        answer.append(f"""customer_relationship_manager.delete_customer.func(customer_id="{row['customer_id']}")""")
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
            f"""customer_relationship_manager.update_customer.func(customer_id="{row['customer_id']}", field="status", new_value="Lost")"""
        )
    return {
        **base_dict,
        "weeks": weeks,
        "answer": answer,
    }

CALENDAR_TEMPLATES = [
    {
        "query": "Cancel my first meeting on {natural_language_date}",
        "alternative_queries": [
            "Delete my first meeting on {natural_language_date}",
            "can you cancel my first meeting on {natural_language_date}",
        ],
        "logic": first_event_logic,
    },
    {
        "query": "Change the name of the last event on {natural_language_date} to {event_name}",
        "alternative_queries": [
            "Rename the last event on {natural_language_date} to {event_name}",
            "Can you change the name of the last event on {natural_language_date} to {event_name}",
        ],
        "logic": last_event_name_change_logic,
    },
    {
        "query": "Push back my first meeting with {name} on {natural_language_date} by {duration}s",
        "alternative_queries": [
            "Delay my first meeting with {name} on {natural_language_date} by {duration}s",
            "please move my first meeting with {name} on {natural_language_date} by {duration}s",
        ],
        "logic": delay_first_meeting_logic,
    },
    {
        "query": "Cancel the next {event_name} meeting",
        "alternative_queries": [
            "Delete the next {event_name} meeting",
            "Can you cancel the next {event_name} meeting",
        ],
        "logic": cancel_event_logic,
    },
    {
        "query": "Rename the next {event_name} meeting to {new_event_name}",
        "alternative_queries": [
            "Change the name of the next {event_name} meeting to {new_event_name}",
            "can you rename the next {event_name} meeting to {new_event_name}",
        ],
        "logic": rename_event_logic,
    },
    {
        "query": "Cancel my next meeting with {name}",
        "alternative_queries": [
            "{name} is off sick. Can you cancel my next meeting with them?",
            "I need to cancel my next meeting with {name}. Can you do that for me please?",
        ],
        "logic": cancel_next_event_with_name_logic,
    },
    {
        "query": "If I haven't met with {name} in the last {duration} days, schedule a 30-minute meeting called 'catch-up' for my first free slot from tomorrow",
        "alternative_queries": [
            "I think I might need to catch up with {name}. Can you check if I've met with them in the last {duration} days? If not, schedule a 30-minute meeting for my first free slot from tomorrow",
            "have I met with {name} in the last {duration} days? If not, schedule a 30-minute meeting called 'catch-up' for my first free slot from tomorrow",
        ],
        "logic": check_last_meeting_with_name_schedule_30_tomorrow,
    },
    {
        "query": "Cancel my meetings on {next_day} {before_or_after} {natural_language_time}",
        "alternative_queries": [
            "Delete my meetings on {next_day} {before_or_after} {natural_language_time}",
            "something came up. Can you cancel my meetings on {next_day} {before_or_after} {natural_language_time}?",
        ],
        "logic": cancel_events_on_day_logic,
    },
    {
        "query": "Cancel all future meetings with {name}",
        "alternative_queries": [
            "{name} is leaving the company. Can you cancel all future meetings with them?",
            "I need to cancel all future meetings with {name}. Can you do that for me please?",
        ],
        "logic": cancel_all_future_meetings_with_person_logic,
    },
    {
        "query": "Cancel future {event_name} meetings",
        "alternative_queries": [
            "Delete all the future {event_name} meetings",
            "We've decided we don't need any any more {event_name} meetings. Can you cancel all future ones?",
        ],
        "logic": cancel_future_meetings_with_name_logic,
    },
    {
        "query": "Create a {duration} event called {event_name} on {natural_language_date} at {natural_language_time} with {name}",
        "alternative_queries": [
            "I haven't met with {name} in a while. Can you schedule a {duration} event called {event_name} on {natural_language_date} at {natural_language_time}?",
            "I need to catch up with {name}. can you schedule a {duration} event called {event_name} on {natural_language_date} at {natural_language_time}?",
        ],
        "logic": create_event_logic,
    },
]
CRM_TEMPLATES = [
    {
        "query": "Update the status of {current_customer_name} to {new_status_natural_language} in the crm",
        "alternative_queries": [
            "{current_customer_name} has moved to {new_status_natural_language} status. Can you update that in the crm?",
            "We've got a new customer that's moved to {new_status_natural_language} status. Can you update {current_customer_name} to {new_status_natural_language} in the crm?",
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
