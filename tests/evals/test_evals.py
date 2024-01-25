import pytest
from src.tools.toolkits import tool_information
from src.evals.utils import is_correct


# Test cases
@pytest.mark.parametrize(
    "row, expected",
    [
        (
            {
                "prediction": "calendar.create_event({'id': '123'}), other.function()",
                "ground_truth": "calendar.create_event({'id': '123'})",
                "stopped": False,
            },
            True,
        ),
        (
            {
                "prediction": "calendar.delete_event({'id': '456'}), other.function()",
                "ground_truth": "calendar.create_event({'id': '123'})",
                "stopped": False,
            },
            False,
        ),
        (
            {
                "prediction": "other.function()",
                "ground_truth": "other.function()",
                "stopped": False,
            },
            True,
        ),
        (
            {
                "prediction": "other.function(), calendar.delete_event({'id': '789'})",
                "ground_truth": "other.function()",
                "stopped": False,
            },
            False,
        ),
        (
            {
                "prediction": "calendar.delete_event({'id': '456'})",
                "ground_truth": "calendar.delete_event({'id': '999'})",
                "stopped": False,
            },
            False,
        ),
    ],
)
def test_is_correct(row, expected):
    assert is_correct(row) == expected
