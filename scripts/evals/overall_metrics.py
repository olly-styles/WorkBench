import os
import sys
import argparse

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
from src.evals.utils import AVAILABLE_LLMS, get_latest_results_from_dir

# ignore pandas warning
import warnings

warnings.filterwarnings("ignore")

results_root_dir = os.path.join("data", "results")
full_tools_list = [
    "multi_domain",
    "email",
    "calendar",
    "analytics",
    "project_management",
    "customer_relationship_manager",
]


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    "--tools",
    action="append",
    default=[],
    help=f"Call with --tools <tool 1> --tools <tool 2> etc. Defaults to {full_tools_list}.",
)
arg_parser.add_argument(
    "--models",
    action="append",
    default=[],
    help=f"Call with --models <model 1> --models <model 2> etc. Defaults to {AVAILABLE_LLMS}.",
)
arg_parser.add_argument(
    "--print_errors",
    action="store_true",
    help="Print errors when calculating metrics.",
    default=False,
)
arg_parser.add_argument(
    "--domain_only",
    action="store_true",
    help="Only consider domain specific tools.",
    default=False,
)

args = arg_parser.parse_args()
all_tools_in_prompt = not args.domain_only

if __name__ == "__main__":
    tools = args.tools if len(args.tools) else full_tools_list
    models = args.models if len(args.models) else AVAILABLE_LLMS
    for model in models:
        total_correct = 0
        total_incorrect = 0
        total_side_effects = 0
        total_correct_no_actions = 0
        total_incorrect_no_actions = 0
        total_correct_non_zero_actions = 0
        total_incorrect_non_zero_actions = 0
        total_correct_two_or_more_actions = 0
        total_incorrect_two_or_more_actions = 0
        total_context_window_errors = 0
        for tool in tools:
            results = get_latest_results_from_dir(results_root_dir, model, tool, args.print_errors, all_tools_in_prompt)
            if results is None:
                continue
            else:
                (
                    correct,
                    incorrect,
                    side_effects,
                    correct_no_actions,
                    incorrect_no_actions,
                    correct_non_zero_actions,
                    incorrect_non_zero_actions,
                    correct_two_or_more_actions,
                    incorrect_two_or_more_actions,
                    num_context_window_errors,
                ) = results
            total_correct += correct
            total_incorrect += incorrect
            total_side_effects += side_effects
            total_correct_no_actions += correct_no_actions
            total_incorrect_no_actions += incorrect_no_actions
            total_correct_non_zero_actions += correct_non_zero_actions
            total_incorrect_non_zero_actions += incorrect_non_zero_actions
            total_correct_two_or_more_actions += correct_two_or_more_actions
            total_incorrect_two_or_more_actions += incorrect_two_or_more_actions
            total_context_window_errors += num_context_window_errors
        if total_correct + total_incorrect == 0:
            print(f"No results found for {model}.")
            continue
        print()
        print(f"Calculating overall metrics for {model}")
        print(f"Overall metrics for {model}:")
        print(
            f"Accuracy (%): {total_correct / (total_correct + total_incorrect) * 100} ({total_correct} / {total_correct + total_incorrect})"
        )
        print(
            f"Side effects (%): {total_side_effects / (total_correct + total_incorrect) * 100} ({total_side_effects} / {total_correct + total_incorrect})"
        )
        print(
            f"Accuracy without actions (%): {total_correct_no_actions / (total_correct_no_actions + total_incorrect_no_actions) * 100} ({total_correct_no_actions} / {total_correct_no_actions + total_incorrect_no_actions})"
        )
        print(
            f"Accuracy with non-zero actions (%): {total_correct_non_zero_actions / (total_correct_non_zero_actions + total_incorrect_non_zero_actions) * 100} ({total_correct_non_zero_actions} / {total_correct_non_zero_actions + total_incorrect_non_zero_actions})"
        )
        print(
            f"Accuracy with two or more actions (%): {total_correct_two_or_more_actions / (total_correct_two_or_more_actions + total_incorrect_two_or_more_actions) * 100} ({total_correct_two_or_more_actions} / {total_correct_two_or_more_actions + total_incorrect_two_or_more_actions})"
        )
        print(
            f"Context window errors (%): {total_context_window_errors / (total_correct + total_incorrect) * 100} ({total_context_window_errors} / {total_correct + total_incorrect})"
        )
