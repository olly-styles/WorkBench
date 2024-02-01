echo multi_domain_questions_and_answers GPT-4
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/multi_domain_questions_and_answers.csv" --predictions_path "data/results/answers_gpt-4-0125-preview2024-01-31 16:01:08.987939.csv"
echo email_questions_and_answers_single_action GPT-4
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/email_questions_and_answers_single_action.csv" --predictions_path "data/results/answers_gpt-4-0125-preview2024-01-31 16:07:37.828123.csv"
echo email_questions_and_answers_multi_action GPT-4
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/email_questions_and_answers_multi_action.csv" --predictions_path "data/results/answers_gpt-4-0125-preview2024-01-31 16:13:20.402320.csv"
echo calendar_questions_and_answers_single_action GPT-4
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/calendar_questions_and_answers_single_action.csv" --predictions_path "data/results/answers_gpt-4-0125-preview2024-01-31 16:19:24.017571.csv"
echo calendar_questions_and_answers_multi_action GPT-4
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/calendar_questions_and_answers_multi_action.csv" --predictions_path "data/results/answers_gpt-4-0125-preview2024-01-31 16:31:47.145534.csv"
echo multi_domain_questions_and_answers GPT-3.5
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/multi_domain_questions_and_answers.csv" --predictions_path "data/results/answers_gpt-3.5-turbo-instruct2024-01-31 16:33:34.038610.csv"
echo email_questions_and_answers_single_action GPT-3.5
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/email_questions_and_answers_single_action.csv" --predictions_path "data/results/answers_gpt-3.5-turbo-instruct2024-01-31 16:35:08.445972.csv"
echo email_questions_and_answers_multi_action GPT-3.5
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/email_questions_and_answers_multi_action.csv" --predictions_path "data/results/answers_gpt-3.5-turbo-instruct2024-01-31 16:36:43.085882.csv"
echo calendar_questions_and_answers_single_action GPT-3.5
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/calendar_questions_and_answers_single_action.csv" --predictions_path "data/results/answers_gpt-3.5-turbo-instruct2024-01-31 16:39:35.852672.csv"
echo calendar_questions_and_answers_multi_action GPT-3.5
python scripts/evals/calculate_metrics.py --ground_truth_path "data/processed/calendar_questions_and_answers_multi_action.csv" --predictions_path "data/results/answers_gpt-3.5-turbo-instruct2024-01-31 16:41:36.555531.csv"
