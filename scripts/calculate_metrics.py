import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--answers_path", type=str, help="path to answers csv")
args = parser.parse_args()

predictions = pd.read_csv(args.answers_path)
predictions = predictions.rename(columns={"answer": "prediction"})

ground_truth = pd.read_csv("data/processed/questions_and_answers.csv")
ground_truth = ground_truth.rename(columns={"answer": "ground_truth"})

assert len(predictions) == len(
    ground_truth
), "Number of predictions does not match number of ground truth answers."

df = predictions.merge(ground_truth, on="question")


# print out the questions that were not answered correctly
for i, row in df[df["prediction"] != df["ground_truth"]].iterrows():
    print(f"Question: {row['question']}")
    print(f"Prediction  : {row['prediction']}")
    print(f"Ground truth: {row['ground_truth']}")
    print()

print(f"Accuracy: {round((df['prediction'] == df['ground_truth']).mean() * 100, 2)}%")
