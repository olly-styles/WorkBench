import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, get_type_hints

_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def _type_to_json_schema_type(tp: Any) -> str:
    return _TYPE_MAP.get(tp, "string")


def _title_case(name: str) -> str:
    return " ".join(word.capitalize() for word in name.split("_"))


def _build_args_schema(func: Callable[..., Any]) -> dict[str, Any]:
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    schema: dict[str, Any] = {}
    for param_name, param in sig.parameters.items():
        tp = hints.get(param_name, str)
        entry: dict[str, Any] = {"title": _title_case(param_name), "type": _type_to_json_schema_type(tp)}
        if param.default is not inspect.Parameter.empty:
            entry["default"] = param.default
        schema[param_name] = entry
    return schema


def _build_signature_str(name: str, func: Callable[..., Any]) -> str:
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    parts = []
    for param_name, param in sig.parameters.items():
        tp = hints.get(param_name)
        annotation = ""
        if tp is not None:
            annotation = f": {inspect.formatannotation(tp)}"
        if param.default is not inspect.Parameter.empty:
            parts.append(f"{param_name}{annotation} = {param.default!r}")
        else:
            parts.append(f"{param_name}{annotation}")
    ret = hints.get("return")
    ret_str = f" -> {inspect.formatannotation(ret)}" if ret else ""
    return f"{name}({', '.join(parts)}){ret_str}"


@dataclass
class Tool:
    name: str
    func: Callable[..., Any]
    description: str
    args_schema: dict[str, Any]
    signature_str: str

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)


def tool(name: str) -> Callable[..., Tool]:
    def decorator(func: Callable[..., Any]) -> Tool:
        return Tool(
            name=name,
            func=func,
            description=func.__doc__ or "",
            args_schema=_build_args_schema(func),
            signature_str=_build_signature_str(name, func),
        )

    return decorator


def render_tool_description(t: Tool) -> str:
    return f"{t.name}: {t.signature_str} - {t.description}, args: {t.args_schema}"


def _args_schema_to_json_schema(args_schema: dict[str, Any]) -> dict[str, Any]:
    """Convert internal args_schema to a JSON Schema ``properties`` + ``required`` block."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    for param_name, entry in args_schema.items():
        prop: dict[str, Any] = {"type": entry["type"], "description": entry.get("title", param_name)}
        properties[param_name] = prop
        if "default" not in entry:
            required.append(param_name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def tool_to_openai_schema(t: Tool) -> dict[str, Any]:
    """Convert a Tool to an OpenAI function-calling tool schema."""
    return {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description,
            "parameters": _args_schema_to_json_schema(t.args_schema),
        },
    }
