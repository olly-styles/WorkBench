"""CLI entry points for WorkBench.

Registered via [project.scripts] in pyproject.toml so they can be invoked
directly: workbench-inference, workbench-evaluate, workbench-generate-data.
"""

from __future__ import annotations

import argparse
import ast
import logging
import warnings
from dataclasses import fields
from pathlib import Path


def inference() -> None:
    """Run model inference on tasks (workbench-inference)."""
    from dotenv import load_dotenv

    load_dotenv(Path(".env"))

    import pandas as pd

    from src.evals.inference import AVAILABLE_LLMS, generate_results
    from src.evals.metrics import calculate_metrics

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Run model inference on tasks")
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="model name. Must be one of " + ", ".join(AVAILABLE_LLMS),
    )
    parser.add_argument(
        "--tasks_path",
        type=str,
        required=True,
        help="path to tasks and outcomes csv",
    )
    parser.add_argument(
        "--tool_selection",
        type=str,
        default="all",
        help="tool selection method: 'all' or 'domains'",
    )
    parser.add_argument("--workers", type=int, default=64, help="number of parallel workers")
    parser.add_argument("--log_traces", action="store_true", help="save full LLM traces as JSON")
    parser.add_argument(
        "--act_without_confirmation",
        action="store_true",
        help="add system prompt suffix instructing the model to act without asking for confirmation",
    )
    parser.add_argument(
        "--structured_outputs",
        action="store_true",
        help="use native API tool calling instead of ReAct text parsing",
    )

    args = parser.parse_args()
    ground_truth = pd.read_csv(args.tasks_path)
    ground_truth["outcome"] = ground_truth["outcome"].apply(ast.literal_eval)
    results = generate_results(
        args.tasks_path,
        args.model_name,
        args.tool_selection,
        workers=args.workers,
        log_traces=args.log_traces,
        act_without_confirmation=args.act_without_confirmation,
        structured_outputs=args.structured_outputs,
    )
    calculate_metrics(ground_truth, results)


def evaluate() -> None:
    """Calculate evaluation metrics (workbench-evaluate)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    warnings.filterwarnings("ignore")

    from src.evals.inference import AVAILABLE_LLMS
    from src.evals.metrics import ResultsSummary, get_latest_results_from_dir

    full_tools_list = [
        "multi_domain",
        "email",
        "calendar",
        "analytics",
        "project_management",
        "customer_relationship_manager",
    ]

    parser = argparse.ArgumentParser(description="Calculate evaluation metrics")
    parser.add_argument("--tools", action="append", default=[], help="tools to evaluate")
    parser.add_argument("--models", action="append", default=[], help="models to evaluate")
    parser.add_argument("--print_errors", action="store_true", default=False)
    parser.add_argument("--all_tools", action="store_true", default=False)

    args = parser.parse_args()
    tools = args.tools or full_tools_list
    models = args.models or AVAILABLE_LLMS
    results_root_dir = "data/results"

    for model in models:
        totals = ResultsSummary(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        for tool in tools:
            results = get_latest_results_from_dir(
                results_root_dir,
                model,
                tool,
                args.print_errors,
                args.all_tools,
            )
            if results is None:
                continue
            for field in fields(totals):
                setattr(totals, field.name, getattr(totals, field.name) + getattr(results, field.name))
        total = totals.num_correct + totals.num_incorrect
        if total == 0:
            logger.warning("No results found for %s.", model)
            continue
        logger.info("Overall metrics for %s:", model)
        logger.info("Accuracy (%%): %s (%s / %s)", totals.num_correct / total * 100, totals.num_correct, total)
        logger.info(
            "Side effects (%%): %s (%s / %s)",
            totals.num_side_effects / total * 100,
            totals.num_side_effects,
            total,
        )
        if args.print_errors:
            total_no_actions = totals.num_correct_no_actions + totals.num_incorrect_no_actions
            total_non_zero = totals.num_correct_non_zero_actions + totals.num_incorrect_non_zero_actions
            total_two_or_more = totals.num_correct_two_or_more_actions + totals.num_incorrect_two_or_more_actions
            logger.info(
                "Accuracy without actions (%%): %s (%s / %s)",
                totals.num_correct_no_actions / total_no_actions * 100,
                totals.num_correct_no_actions,
                total_no_actions,
            )
            logger.info(
                "Accuracy with non-zero actions (%%): %s (%s / %s)",
                totals.num_correct_non_zero_actions / total_non_zero * 100,
                totals.num_correct_non_zero_actions,
                total_non_zero,
            )
            logger.info(
                "Accuracy with two or more actions (%%): %s (%s / %s)",
                totals.num_correct_two_or_more_actions / total_two_or_more * 100,
                totals.num_correct_two_or_more_actions,
                total_two_or_more,
            )
            logger.info(
                "Context window errors (%%): %s (%s / %s)",
                totals.num_context_window_errors / total * 100,
                totals.num_context_window_errors,
                total,
            )
        logger.info("==============================")


def generate_data() -> None:
    """Generate sandbox databases and task/outcome data (workbench-generate-data)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    warnings.filterwarnings("ignore")

    import scripts.data_generation.sandbox_databases.generate_analytics_data as gen_analytics
    import scripts.data_generation.sandbox_databases.generate_calendar_data as gen_calendar
    import scripts.data_generation.sandbox_databases.generate_customer_relationship_manager_data as gen_crm
    import scripts.data_generation.sandbox_databases.generate_email_data as gen_email
    import scripts.data_generation.sandbox_databases.generate_project_management_data as gen_pm
    import scripts.data_generation.task_outcome_generation.generate_analytics_task_and_outcome as to_analytics
    import scripts.data_generation.task_outcome_generation.generate_calendar_task_and_outcome as to_calendar
    import scripts.data_generation.task_outcome_generation.generate_customer_relationship_manager_task_and_outcome as to_crm
    import scripts.data_generation.task_outcome_generation.generate_email_task_and_outcome as to_email
    import scripts.data_generation.task_outcome_generation.generate_multi_domain_task_and_outcome as to_multi
    import scripts.data_generation.task_outcome_generation.generate_project_management_task_and_outcome as to_pm

    sandbox_domains = {
        "calendar": gen_calendar,
        "analytics": gen_analytics,
        "crm": gen_crm,
        "email": gen_email,
        "project_management": gen_pm,
    }
    for name, module in sandbox_domains.items():
        logger.info("Generating %s sandbox data...", name)
        module.generate_data()

    task_domains = {
        "analytics": to_analytics,
        "calendar": to_calendar,
        "crm": to_crm,
        "email": to_email,
        "project_management": to_pm,
        "multi_domain": to_multi,
    }
    for name, module in task_domains.items():
        logger.info("Generating %s task and outcome data...", name)
        module.generate_task_and_outcome()
