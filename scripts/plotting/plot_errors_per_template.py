import argparse
import ast

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from scripts.evals.calculate_all_metrics import full_tools_list
from src.evals.metrics import calculate_metrics, get_latest_results_path

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="gpt-5-nano", help="Model name to plot errors for.")

RESULTS_ROOT_DIR = "data/results/"

if __name__ == "__main__":
    args = parser.parse_args()
    MODEL = args.model

    percentage_correct = []
    for tool in full_tools_list:
        results_paths = get_latest_results_path(RESULTS_ROOT_DIR, MODEL, tool)
        if results_paths is None:
            continue
        model_results_path, ground_truth_path = results_paths
        predictions = pd.read_csv(model_results_path, dtype=str, engine="python", on_bad_lines="warn")
        ground_truth = pd.read_csv(ground_truth_path, dtype=str)
        ground_truth["outcome"] = ground_truth["outcome"].apply(ast.literal_eval)
        predictions["function_calls"] = predictions["function_calls"].apply(ast.literal_eval)
        df = calculate_metrics(ground_truth, predictions, print_errors=False)
        percentage_correct.append(df.groupby("base_template")["correct"].mean().to_numpy() * 100)
        # print base template with 0% correct
        templates_with_0_percent_correct = (
            df.groupby("base_template")["correct"].mean().loc[df.groupby("base_template")["correct"].mean() == 0]
        )
        print(f"Tool: {tool}")
        print("Base templates with 0% correct:")
        for template in templates_with_0_percent_correct.index:
            print(template)

    # flatten
    percentage_correct = [item for sublist in percentage_correct for item in sublist]

    # print number of template where percentage correct is 100 or 0, and how many are not either 100 or 0
    print(
        f"Number of templates where percentage correct is 100 or 0: {percentage_correct.count(100) + percentage_correct.count(0)} out of {len(percentage_correct)} ({(percentage_correct.count(100) + percentage_correct.count(0)) / len(percentage_correct) * 100:.1f}%)"
    )
    print(
        f"Number of templates where percentage correct is neither 100 or 0: {len(percentage_correct) - percentage_correct.count(100) - percentage_correct.count(0)} out of {len(percentage_correct)} ({(len(percentage_correct) - percentage_correct.count(100) - percentage_correct.count(0)) / len(percentage_correct) * 100:.1f}%)"
    )

    # Group percentage_correct by value and count
    percentage_correct_df = pd.DataFrame(percentage_correct, columns=pd.Index(["percentage_correct"]))
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
