import random
from typing import Any


def generate_task_and_outcome(template: dict[str, Any]) -> dict[str, Any]:
    """Generates task and outcome from template."""
    logic = template["logic"]()
    possible_tasks = [template["task"]] + template.get("alternative_tasks", [])
    task_template = random.choice(possible_tasks)
    return {
        "task": task_template.format(**logic),
        "outcome": logic["outcome"],
        "base_template": template["task"],
        "chosen_template": task_template,
        "domains": template.get("domains", []),
    }


def generate_all_tasks_and_outcomes(
    templates: list[dict[str, Any]],
    max_tasks_per_template: int,
    verbose: bool = False,
    max_attempts_per_template: int = 10000,
) -> list[dict[str, Any]]:
    """Generates a limited number of unique tasks and outcomes for each template."""
    generated_tasks_and_outcomes: list[dict[str, Any]] = []
    seen_tasks: set[str] = set()
    for template in templates:
        tasks_generated_for_template = 0
        attempts = 0
        while tasks_generated_for_template < max_tasks_per_template:
            if attempts >= max_attempts_per_template:
                raise ValueError(
                    f"Could only generate {tasks_generated_for_template} of {max_tasks_per_template} unique tasks "
                    f"for template {template['task']!r} after {attempts} attempts. The template's logic likely "
                    f"cannot produce that many distinct tasks."
                )
            attempts += 1
            t_and_o = generate_task_and_outcome(template)
            if t_and_o["task"] not in seen_tasks:
                seen_tasks.add(t_and_o["task"])
                generated_tasks_and_outcomes.append(t_and_o)
                tasks_generated_for_template += 1

    if verbose:
        for task_and_outcome in generated_tasks_and_outcomes:
            print(f"Base template:   {task_and_outcome['base_template']}")
            print(f"Chosen template: {task_and_outcome['chosen_template']}")
            print(f"Task:            {task_and_outcome['task']}")
            print(f"Outcome:         {task_and_outcome['outcome']}")
            print("--------------------------------------------")

    return generated_tasks_and_outcomes
