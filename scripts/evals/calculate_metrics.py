import pandas as pd
import argparse
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import has_side_effects, is_correct

parser = argparse.ArgumentParser()
parser.add_argument(
    "--predictions_path",
    type=str,
    help="path to answers csv. By default this is stored in data/results/",
    required=True,
)
parser.add_argument(
    "--ground_truth_path",
    type=str,
    help="path to ground truth csv. By default this is stored in data/processed/",
    required=True,
)
args = parser.parse_args()

predictions = pd.read_csv(args.predictions_path)
predictions = predictions.rename(columns={"function_calls": "prediction"})
predictions = predictions.fillna("")

ground_truth = pd.read_csv(args.ground_truth_path, dtype=str)
ground_truth = ground_truth.rename(columns={"answer": "ground_truth"})


df = predictions.merge(ground_truth, on="question")
assert (
    len(predictions) == len(ground_truth) == len(df)
), "Number of predictions does not match number of ground truth answers. Check that the predictions and ground truth are for the same questions."

df["correct"] = df.apply(is_correct, axis=1)
df["has_side_effects"] = df.apply(has_side_effects, axis=1)

# print out the questions that were not answered correctly
for index, row in df[~df["correct"]].iterrows():
    print(f"Question: {row['question']}")
    print(f"Prediction: {row['prediction']}")
    print(f"Ground truth: {row['ground_truth']}")
    print(f"Has side effects: {row['has_side_effects']}")
    print("")

# print accuracy as a percentage to 2dp
print(f"Accuracy: {round(df['correct'].mean() * 100, 2)}%")
# print number of side effects as a percentage to 2dp
print(f"Side effects: {round(df['has_side_effects'].mean() * 100, 2)}% of predictions")
