import os
import sys
import ast
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from scripts.evals.overall_metrics import full_tools_list
from src.evals.utils import calculate_metrics, get_latest_results_path
import pandas as pd

RESULTS_ROOT_DIR = "data/results/"
MODEL = "gpt-4"

precentage_correct = []
for tool in full_tools_list:
    model_results_path, ground_truth_path = get_latest_results_path(RESULTS_ROOT_DIR, MODEL, tool)
    predictions = pd.read_csv(model_results_path, dtype=str)
    ground_truth = pd.read_csv(ground_truth_path, dtype=str)
    ground_truth["answer"] = ground_truth["answer"].apply(ast.literal_eval)
    predictions["function_calls"] = predictions["function_calls"].apply(ast.literal_eval)
    df = calculate_metrics(ground_truth, predictions, print_errors=False)
    precentage_correct.append(df.groupby("base_template")["correct"].mean().values * 100)
    # print base template with 0% correct
    templates_with_0_percent_correct = (
        df.groupby("base_template")["correct"].mean().loc[df.groupby("base_template")["correct"].mean() == 0]
    )
    print(f"Tool: {tool}")
    print(f"Base templates with 0% correct:")
    for template in templates_with_0_percent_correct.index:
        print(template)

# flatten
precentage_correct = [item for sublist in precentage_correct for item in sublist]

# print number of template where percentage correct is 100 or 0, and how many are not either 100 or 0
print(
    f"Number of templates where percentage correct is 100 or 0: {precentage_correct.count(100) + precentage_correct.count(0)} out of {len(precentage_correct)} ({(precentage_correct.count(100) + precentage_correct.count(0)) / len(precentage_correct) * 100:.1f}%)"
)
print(
    f"Number of templates where percentage correct is neither 100 or 0: {len(precentage_correct) - precentage_correct.count(100) - precentage_correct.count(0)} out of {len(precentage_correct)} ({(len(precentage_correct) - precentage_correct.count(100) - precentage_correct.count(0)) / len(precentage_correct) * 100:.1f}%)"
)

# Group percentage_correct by value and count
percentage_correct_df = pd.DataFrame(precentage_correct, columns=["percentage_correct"])
percentage_correct_df["count"] = 1
percentage_correct_df = percentage_correct_df.groupby("percentage_correct").count().reset_index()


# increase fontsize
sns.set(font_scale=1.8)

plt.figure(figsize=(12, 6))
ax = sns.barplot(x="percentage_correct", y="count", data=percentage_correct_df)
ax.set(xlabel="Percentage tasks completed correctly", ylabel="Number of templates")
ax.set_xticklabels([f"{x}%" for x in range(0, 200, 10)])
plt.tight_layout()


plt.savefig("data/plots/percentage_correct_per_template.png")
