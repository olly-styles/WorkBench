import itertools

import pytest

from src.data_generation.data_generation_utils import generate_all_tasks_and_outcomes


def test_raises_when_template_cannot_produce_enough_unique_tasks():
    template = {
        "task": "Do thing {n}",
        "alternative_tasks": [],
        "domains": ["calendar"],
        "logic": lambda: {"outcome": [], "n": 1},
    }
    with pytest.raises(ValueError, match="unique tasks"):
        generate_all_tasks_and_outcomes([template], max_tasks_per_template=10, max_attempts_per_template=50)


def test_generates_requested_number_of_unique_tasks():
    counter = itertools.count()
    template = {
        "task": "Do thing {n}",
        "alternative_tasks": [],
        "domains": ["calendar"],
        "logic": lambda: {"outcome": [], "n": next(counter)},
    }
    result = generate_all_tasks_and_outcomes([template], max_tasks_per_template=5, max_attempts_per_template=50)
    assert len(result) == 5
    assert len({t["task"] for t in result}) == 5
