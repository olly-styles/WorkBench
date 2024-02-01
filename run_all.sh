python scripts/inference/generate_answers.py --model_name gpt-4-0125-preview --questions_path "data/processed/multi_domain_questions_and_answers.csv";
python scripts/inference/generate_answers.py --model_name gpt-4-0125-preview --questions_path "data/processed/email_questions_and_answers_single_action.csv";
python scripts/inference/generate_answers.py --model_name gpt-4-0125-preview --questions_path "data/processed/email_questions_and_answers_multi_action.csv";
python scripts/inference/generate_answers.py --model_name gpt-4-0125-preview --questions_path "data/processed/calendar_questions_and_answers_single_action.csv";
python scripts/inference/generate_answers.py --model_name gpt-4-0125-preview --questions_path "data/processed/calendar_questions_and_answers_multi_action.csv";
python scripts/inference/generate_answers.py --model_name gpt-3.5-turbo-instruct --questions_path "data/processed/multi_domain_questions_and_answers.csv";
python scripts/inference/generate_answers.py --model_name gpt-3.5-turbo-instruct --questions_path "data/processed/email_questions_and_answers_single_action.csv";
python scripts/inference/generate_answers.py --model_name gpt-3.5-turbo-instruct --questions_path "data/processed/email_questions_and_answers_multi_action.csv";
python scripts/inference/generate_answers.py --model_name gpt-3.5-turbo-instruct --questions_path "data/processed/calendar_questions_and_answers_single_action.csv";
python scripts/inference/generate_answers.py --model_name gpt-3.5-turbo-instruct --questions_path "data/processed/calendar_questions_and_answers_multi_action.csv";


