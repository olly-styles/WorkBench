import ast

import matplotlib.pyplot as plt
import pandas as pd

# File paths
file_paths = [
    "data/processed/tasks_and_outcomes/analytics_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/calendar_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/customer_relationship_manager_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/email_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/multi_domain_tasks_and_outcomes.csv",
    "data/processed/tasks_and_outcomes/project_management_tasks_and_outcomes.csv",
]

# Load the data from each file and calculate the length of the outcome list
outcome_lengths = []
for file_path in file_paths:
    df = pd.read_csv(file_path)
    # Extract the length of the outcome list from each row and append to outcome_lengths list
    outcome_lengths.extend(df["outcome"].apply(lambda x: len(ast.literal_eval(x))))

# Increase font size
plt.rcParams.update({"font.size": 26})


# Plotting the histogram of the length of the outcome list
plt.figure(figsize=(15, 5))
plt.hist(
    outcome_lengths, bins=range(0, max(outcome_lengths) + 2), align="left", color="mediumseagreen", edgecolor="black"
)
plt.xlabel("Number of actions", labelpad=20)
plt.ylabel("Frequency", labelpad=20)


plt.xticks(range(0, max(outcome_lengths) + 1))
plt.yticks(range(0, int(max(plt.gca().get_ylim()) * 1.1), 100))
# tight_layout() adjusts the plot to fit into the figure area
plt.tight_layout()
# no margin at the bottom
plt.subplots_adjust(bottom=0.22)

# no border around top and right
plt.gca().spines["top"].set_visible(False)
plt.gca().spines["right"].set_visible(False)

plt.savefig("data/plots/outcome_action_lengths.png")
