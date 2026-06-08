from __future__ import annotations

import ast
import logging

import pandas as pd

from src.tools.state import get_state, reset_state
from src.tools.tool import Tool
from src.tools.toolkits import all_tools

logger = logging.getLogger(__name__)

_TOOL_DISPATCH: dict[str, Tool] = {t.name: t for t in all_tools}
_ALLOWED_TOOL_NAMES: frozenset[str] = frozenset(_TOOL_DISPATCH.keys())


def _escape_arg_value(v: str) -> str:
    return str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def convert_intermediate_step_to_function_call(tool_name: str, tool_input: dict[str, str]) -> str:
    args = [f'{k}="{_escape_arg_value(v)}"' for k, v in tool_input.items()]
    return f"{tool_name}.func({', '.join(args)})"


def _parse_and_dispatch(action: str) -> bool:
    tree = ast.parse(action, mode="eval")
    call = tree.body
    if not isinstance(call, ast.Call):
        return False

    func_parts: list[str] = []
    node = call.func
    while isinstance(node, ast.Attribute):
        func_parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        func_parts.append(node.id)
    func_parts.reverse()

    parts = func_parts[:-1] if len(func_parts) >= 3 and func_parts[-1] == "func" else func_parts
    tool_name = ".".join(parts)

    if tool_name not in _ALLOWED_TOOL_NAMES:
        logger.warning("Rejected disallowed tool name: %s", tool_name)
        return False

    tool = _TOOL_DISPATCH[tool_name]

    kwargs: dict[str, str] = {}
    for kw in call.keywords:
        if kw.arg is None:
            continue
        value = ast.literal_eval(kw.value)
        kwargs[kw.arg] = str(value)

    tool.func(**kwargs)
    return True


def execute_actions_and_reset_state(
    actions: list[str],
) -> tuple[bool, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Executes a list of actions on the calendar and returns the resulting calendar events.

    Parameters
    ----------
    actions : list
        List of actions to be executed. Each action should be a function call.

    Returns
    -------
    success bool
        True if the actions were executed successfully.
    new_calendar_state pd.DataFrame
        The resulting calendar events after executing the actions.
    new_email_state pd.DataFrame
        The resulting emails after executing the actions.
    new_analytics_state pd.DataFrame
        The resulting analytics data after executing the actions.
    """
    reset_state()

    all_actions_succeeded = True
    for action in actions:
        try:
            dispatched = _parse_and_dispatch(action)
        except (SyntaxError, ValueError, KeyError, AttributeError, TypeError) as e:
            logger.warning("Action failed: %s — %s: %s", action, type(e).__name__, e)
            all_actions_succeeded = False
            continue
        if not dispatched:
            all_actions_succeeded = False

    state = get_state()
    result = (
        all_actions_succeeded,
        state.calendar_events.copy(),
        state.emails.copy(),
        state.plots_data.copy(),
        state.project_tasks.copy(),
        state.crm_data.copy(),
    )

    # Reset the state of the tools
    reset_state()
    return result
