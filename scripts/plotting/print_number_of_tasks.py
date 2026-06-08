from pathlib import Path

import pandas as pd

# Directory containing the data files
data_dir = Path("data/processed/tasks_and_outcomes")

# List of files in the specified directory
files = [
    "analytics_tasks_and_outcomes.csv",
    "calendar_tasks_and_outcomes.csv",
    "customer_relationship_manager_tasks_and_outcomes.csv",
    "email_tasks_and_outcomes.csv",
    "multi_domain_tasks_and_outcomes.csv",
    "project_management_tasks_and_outcomes.csv",
]

# Initialize a dictionary to hold the counts of unique tasks and templates for each file
unique_counts = {}

# Loop through each file and calculate the unique counts
for file in files:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(data_dir / file)

    # Calculate the number of unique tasks and templates
    unique_tasks = df["task"].nunique()
    unique_templates = df["base_template"].nunique()

    # Store the counts in the dictionary
    unique_counts[file] = {"unique_tasks": unique_tasks, "unique_templates": unique_templates}


for file, counts in unique_counts.items():
    print(f"File: {file.split('_')[0]}")
    print(f"Number of unique tasks: {counts['unique_tasks']}")
    print(f"Number of unique templates: {counts['unique_templates']}")
    print()

# print totals
total_unique_tasks = sum(counts["unique_tasks"] for counts in unique_counts.values())
total_unique_templates = sum(counts["unique_templates"] for counts in unique_counts.values())
print(f"Total number of unique tasks: {total_unique_tasks}")
print(f"Total number of unique templates: {total_unique_templates}")
