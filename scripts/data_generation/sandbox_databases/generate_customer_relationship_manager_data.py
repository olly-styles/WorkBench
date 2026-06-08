import json
import random
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

import scripts.data_generation.sandbox_databases.generate_project_management_data as pm_data
from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME

SEED_DATA_DIR = Path(__file__).parent.parent / "seed_data"
CRM_SEED = json.loads((SEED_DATA_DIR / "crm.json").read_text())


# Define a function to generate random customer names
def generate_random_name(first_names: list[str], last_names: list[str]) -> str:
    return random.choice(first_names) + " " + random.choice(last_names)


# Define a function to generate random email addresses
def generate_random_email(name: str) -> str:
    prefix = random.choice(CRM_SEED["company_prefixes"])
    suffix = random.choice(CRM_SEED["company_suffixes"])
    modifier = random.choice(CRM_SEED["company_modifiers"])
    # Format: Prefix+Modifier+Suffix, Prefix+Suffix, Modifier+Suffix (avoid repetitions)
    formats = [f"{prefix}{modifier}{suffix}", f"{prefix}{suffix}", f"{modifier}{suffix}"]
    name_parts = name.lower().split()
    return f"{name_parts[0]}.{name_parts[1]}@{random.choice(formats)}".lower()


def generate_random_phone() -> str:
    return f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


# Define a function to generate random dates for last contact
def generate_random_date(start: pd.Timestamp, end: pd.Timestamp) -> pd.Timestamp:
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_customer_notes(last_contact_date: pd.Timestamp) -> str:
    notes = ""
    for _ in range(random.randint(0, 3)):
        note_date = generate_random_date(HARDCODED_CURRENT_TIME - timedelta(days=60), HARDCODED_CURRENT_TIME)
        note_date = min(note_date, last_contact_date)
        notes += f"{note_date.date()}: {random.choice(CRM_SEED['customer_note_options'])}. "
    return notes


def generate_data() -> None:
    pm_data.load_team_emails()
    random.seed(42)
    np.random.seed(42)
    first_names = CRM_SEED["first_names"]
    last_names = CRM_SEED["last_names"]
    product_interests = CRM_SEED["product_interests"]
    statuses = CRM_SEED["statuses"]

    # Initialize an empty DataFrame
    crm_data = pd.DataFrame(
        columns=pd.Index(
            [
                "customer_id",
                "assigned_to_email",
                "customer_name",
                "customer_email",
                "customer_phone",
                "last_contact_date",
                "product_interest",
                "status",
                "follow_up_by",
                "notes",
            ]
        )
    )

    # Generate random data
    num_customers = 200

    for i in tqdm(range(num_customers)):
        customer_name = generate_random_name(first_names, last_names)
        while customer_name in crm_data["customer_name"].values:
            customer_name = generate_random_name(first_names, last_names)
        customer_id = str(i).zfill(8)
        customer_email = generate_random_email(customer_name)
        customer_phone = generate_random_phone() if np.random.choice([True, False]) else None
        last_contact_date = generate_random_date(HARDCODED_CURRENT_TIME - timedelta(days=60), HARDCODED_CURRENT_TIME)
        follow_up_by = last_contact_date + timedelta(days=random.randint(7, 30))
        notes = generate_customer_notes(last_contact_date)
        product_interest = random.choice(product_interests)
        status = random.choice(statuses)
        assigned_to_email = random.choice(pm_data.sales_team_emails)

        crm_data.loc[len(crm_data)] = [
            customer_id,
            assigned_to_email,
            customer_name,
            customer_email,
            customer_phone,
            last_contact_date,
            product_interest,
            status,
            follow_up_by,
            notes,
        ]

    crm_data = crm_data.sort_values(by="last_contact_date", ascending=False)
    crm_data.to_csv("data/processed/customer_relationship_manager_data.csv", index=False)


if __name__ == "__main__":
    generate_data()
