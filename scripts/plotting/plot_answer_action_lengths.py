import pandas as pd
import matplotlib.pyplot as plt

# File paths
file_paths = [
    "data/processed/queries_and_answers/analytics_queries_and_answers.csv",
    "data/processed/queries_and_answers/calendar_queries_and_answers.csv",
    "data/processed/queries_and_answers/customer_relationship_manager_queries_and_answers.csv",
    "data/processed/queries_and_answers/email_queries_and_answers.csv",
    "data/processed/queries_and_answers/multi_domain_queries_and_answers.csv",
    "data/processed/queries_and_answers/project_management_queries_and_answers.csv",
]

# Load the data from each file and calculate the length of the answer list
answer_lengths = []
for file_path in file_paths:
    df = pd.read_csv(file_path)
    # Extract the length of the answer list from each row and append to answer_lengths list
    answer_lengths.extend(df["answer"].apply(lambda x: len(eval(x))))

# Increase font size
plt.rcParams.update({"font.size": 26})


# Plotting the histogram of the length of the answer list
plt.figure(figsize=(15, 5))
plt.hist(answer_lengths, bins=range(0, max(answer_lengths) + 2), align="left", color="skyblue", edgecolor="black")
plt.xlabel("Number of actions", labelpad=20)
plt.ylabel("Frequency", labelpad=20)


plt.xticks(range(0, max(answer_lengths) + 1))
plt.yticks(range(0, 420, 100))
# tight_layout() adjusts the plot to fit into the figure area
plt.tight_layout()
plt.savefig("data/plots/answer_action_lengths.png")
