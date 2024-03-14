import pandas as pd
import numpy as np
import random
from datetime import timedelta
import os
import sys

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME
from scripts.data_generation.mocked_data.generate_project_management_data import sales_team_emails

random.seed(42)

first_names = [
    "Alex",
    "Jordan",
    "Taylor",
    "Casey",
    "Jamie",
    "Morgan",
    "Cameron",
    "Reese",
    "Quinn",
    "Peyton",
    "Shannon",
    "Rahul",
    "Riley",
    "Jessie",
    "Dakota",
    "Angel",
    "Parker",
    "Avery",
    "Jaden",
    "Kerry",
]
last_names = [
    "Smith",
    "Johnson",
    "Williams",
    "Jones",
    "Brown",
    "Davis",
    "Miller",
    "Wilson",
    "Moore",
    "Taylor",
    "Anderson",
    "Thomas",
    "Jackson",
    "White",
    "Harris",
    "Martin",
    "Thompson",
    "Garcia",
    "Martinez",
    "Robinson",
]


# Define a function to generate random customer names
def generate_random_name(first_names, last_names):
    return random.choice(first_names) + " " + random.choice(last_names)


# Define a function to generate random email addresses
def generate_random_email(name):
    company_prefixes = [
        "Tech",
        "Bio",
        "Green",
        "Quant",
        "Next",
        "Inno",
        "Ultra",
        "Cyber",
        "Future",
        "Pro",
        "Neo",
        "Smart",
        "Alpha",
        "Omni",
        "Solar",
        "Geo",
        "Nano",
        "Aero",
        "Blue",
        "Eco",
    ]
    company_suffixes = [
        "Solutions",
        "Tech",
        "Logics",
        "Systems",
        "Robotics",
        "Energy",
        "Dynamics",
        "Networks",
        "Labs",
        "Analytics",
        "Innovations",
        "Ventures",
        "Designs",
        "Electronics",
        "Software",
        "Hardware",
        "Cloud",
        "Security",
        "Foods",
        "Biotech",
    ]
    company_modifiers = [
        "Global",
        "Dynamic",
        "Interactive",
        "Vision",
        "Peak",
        "Edge",
        "Stream",
        "Link",
        "Wave",
        "Core",
        "Flex",
        "Point",
        "Access",
        "Force",
        "Space",
        "Mind",
        "Port",
        "Path",
        "Scope",
        "Trace",
    ]

    prefix = random.choice(company_prefixes)
    suffix = random.choice(company_suffixes)
    modifier = random.choice(company_modifiers)
    # Format: Prefix+Modifier+Suffix, Prefix+Suffix, Modifier+Suffix (avoid repetitions)
    formats = [f"{prefix}{modifier}{suffix}", f"{prefix}{suffix}", f"{modifier}{suffix}"]
    name_parts = name.lower().split()
    return f"{name_parts[0]}.{name_parts[1]}@{random.choice(formats)}".lower()


def generate_random_phone():
    return f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


# Define a function to generate random dates for last contact
def generate_random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_customer_notes():
    notes = ""
    for _ in range(random.randint(0, 3)):
        notes += f"{generate_random_date(HARDCODED_CURRENT_TIME - timedelta(days=60), HARDCODED_CURRENT_TIME).date()}: {random.choice(['Had a call', 'On holiday', 'Saw the demo', 'Met in person'])}. "
    return notes


# Define product interests
product_interests = ["Software", "Hardware", "Services", "Consulting", "Training"]

# Define crm stages
statuses = ["Qualified", "Won", "Lost", "Lead", "Proposal"]

# Initialize an empty DataFrame
crm_data = pd.DataFrame(
    columns=[
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

# Generate random data
num_customers = 200

for i in range(num_customers):
    customer_name = generate_random_name(first_names, last_names)
    while customer_name in crm_data["customer_name"].values:
        customer_name = generate_random_name(first_names, last_names)
    customer_id = str(i).zfill(8)
    customer_email = generate_random_email(customer_name)
    customer_phone = generate_random_phone() if np.random.choice([True, False]) else None
    last_contact_date = generate_random_date(HARDCODED_CURRENT_TIME - timedelta(days=60), HARDCODED_CURRENT_TIME)
    follow_up_by = last_contact_date + timedelta(days=random.randint(7, 30))
    notes = generate_customer_notes()
    product_interest = random.choice(product_interests)
    status = random.choice(statuses)
    assigned_to_email = random.choice(sales_team_emails)

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

print("Mocked CRM data generated successfully.")
