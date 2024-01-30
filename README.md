# agents-in-the-workplace

Python Version: 3.10.11

## Installation

### Step 1: Install requirements
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Add openai api key
```bash
touch openai_key.txt && echo YOUR_API_KEY > openai_key.txt
```

## Usage
All data, including pre-computed inference results, can be found in the `data` directory.

### Inference:

```bash
python scripts/inference/generate_answers.py --model_name MODEL_NAME --questions_path QUESTIONS_PATH
```

### Evaluation:

```bash
python scripts/evals/calculate_metrics.py --predictions_path PREDICTIONS_PATH --ground_truth_path GROUND_TRUTH_PATH     
```