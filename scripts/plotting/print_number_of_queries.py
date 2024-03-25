import pandas as pd
import os

# Directory containing the data files
data_dir = "data/processed/queries_and_answers"

# List of files in the specified directory
files = [
    "analytics_queries_and_answers.csv",
    "calendar_queries_and_answers.csv",
    "customer_relationship_manager_queries_and_answers.csv",
    "email_queries_and_answers.csv",
    "multi_domain_queries_and_answers.csv",
    "project_management_queries_and_answers.csv",
]

# Initialize a dictionary to hold the counts of unique queries and templates for each file
unique_counts = {}

# Loop through each file and calculate the unique counts
for file in files:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(os.path.join(data_dir, file))

    # Calculate the number of unique queries and templates
    unique_queries = df["query"].nunique()
    unique_templates = df["base_template"].nunique()

    # Store the counts in the dictionary
    unique_counts[file] = {"unique_queries": unique_queries, "unique_templates": unique_templates}


for file, counts in unique_counts.items():
    print(f"File: {file.split('_')[0]}")
    print(f"Number of unique tasks: {counts['unique_queries']}")
    print(f"Number of unique templates: {counts['unique_templates']}")
    print()

# print totals
total_unique_queries = sum(counts["unique_queries"] for counts in unique_counts.values())
total_unique_templates = sum(counts["unique_templates"] for counts in unique_counts.values())
print(f"Total number of unique tasks: {total_unique_queries}")
print(f"Total number of unique templates: {total_unique_templates}")
