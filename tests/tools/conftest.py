import pytest

from src.tools.state import reset_state


@pytest.fixture(autouse=True)
def reset_tool_state():
    reset_state()
    yield
    reset_state()
