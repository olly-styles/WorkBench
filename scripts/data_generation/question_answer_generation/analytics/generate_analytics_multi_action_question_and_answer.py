import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)


random.seed(42)

MULTI_ACTION_TEMPLATES = [
    {
        "question": "Make a plot of page views from {time_min} to {time_max}",
        "answer": """analytics.create_plot.func(time_min='{time_min}', time_max='{time_max}', value_to_plot='page_views')""",
    },
]

# Generate a limited number of unique multi-action questions and answers
max_questions_per_template = 1  # Limit the number of questions per template

if __name__ == "__main__":
    generated_questions_and_answers = []
    for template in MULTI_ACTION_TEMPLATES:
        for _ in range(max_questions_per_template):
            time_min = "2023-10-01"
            time_max = "2023-10-31"
            question = template["question"].format(time_min=time_min, time_max=time_max)
            answer = template["answer"].format(time_min=time_min, time_max=time_max)
            questions = [q["question"] for q in generated_questions_and_answers]
            if question not in questions:
                generated_questions_and_answers.append(
                    {"question": question, "answer": answer, "template": template}
                )
            for question_and_answer in generated_questions_and_answers:
                print(question_and_answer["question"])
                print(question_and_answer["answer"])
                print(question_and_answer["template"])
    df = pd.DataFrame(generated_questions_and_answers)
    df.to_csv(
        "data/processed/analytics_questions_and_answers_multi_action.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )

    