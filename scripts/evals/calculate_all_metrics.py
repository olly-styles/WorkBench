import argparse

# ignore pandas warning
import warnings
from dataclasses import fields

from src.evals.inference import AVAILABLE_LLMS
from src.evals.metrics import ResultsSummary, get_latest_results_from_dir

warnings.filterwarnings("ignore")

results_root_dir = "data/results"
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
    "--all_tools",
    action="store_true",
    help="Include all tools in the prompt (not just domain-specific tools).",
    default=False,
)

if __name__ == "__main__":
    args = arg_parser.parse_args()
    all_tools_in_prompt = args.all_tools
    tools = args.tools or full_tools_list
    models = args.models or AVAILABLE_LLMS
    for model in models:
        totals = ResultsSummary(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        for tool in tools:
            results = get_latest_results_from_dir(results_root_dir, model, tool, args.print_errors, all_tools_in_prompt)
            if results is None:
                continue
            for field in fields(totals):
                setattr(totals, field.name, getattr(totals, field.name) + getattr(results, field.name))
        total = totals.num_correct + totals.num_incorrect
        if total == 0:
            print(f"No results found for {model}.")
            continue
        print()
        print(f"Calculating overall metrics for {model}")
        print(f"Overall metrics for {model}:")
        print(f"Accuracy (%): {totals.num_correct / total * 100} ({totals.num_correct} / {total})")
        print(f"Side effects (%): {totals.num_side_effects / total * 100} ({totals.num_side_effects} / {total})")
        if args.print_errors:
            total_no_actions = totals.num_correct_no_actions + totals.num_incorrect_no_actions
            total_non_zero = totals.num_correct_non_zero_actions + totals.num_incorrect_non_zero_actions
            total_two_or_more = totals.num_correct_two_or_more_actions + totals.num_incorrect_two_or_more_actions
            print(
                f"Accuracy without actions (%): {totals.num_correct_no_actions / total_no_actions * 100} ({totals.num_correct_no_actions} / {total_no_actions})"
            )
            print(
                f"Accuracy with non-zero actions (%): {totals.num_correct_non_zero_actions / total_non_zero * 100} ({totals.num_correct_non_zero_actions} / {total_non_zero})"
            )
            print(
                f"Accuracy with two or more actions (%): {totals.num_correct_two_or_more_actions / total_two_or_more * 100} ({totals.num_correct_two_or_more_actions} / {total_two_or_more})"
            )
            print(
                f"Context window errors (%): {totals.num_context_window_errors / total * 100} ({totals.num_context_window_errors} / {total})"
            )
        print("==============================")
