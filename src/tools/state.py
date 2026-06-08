import threading
from dataclasses import dataclass, fields

import pandas as pd

_CSV_PATHS = {
    "calendar_events": "data/processed/calendar_events.csv",
    "emails": "data/processed/emails.csv",
    "analytics_data": "data/processed/analytics_data.csv",
    "project_tasks": "data/processed/project_tasks.csv",
    "crm_data": "data/processed/customer_relationship_manager_data.csv",
    "directory_emails": "data/raw/email_addresses.csv",
}


def _load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(_CSV_PATHS[name], dtype=str)


def _load_analytics_data() -> pd.DataFrame:
    df = _load_csv("analytics_data")
    df["user_engaged"] = df["user_engaged"] == "True"
    return df


def _load_directory_emails() -> pd.DataFrame:
    return pd.read_csv(_CSV_PATHS["directory_emails"], header=None, names=["email_address"])


@dataclass
class ToolState:
    calendar_events: pd.DataFrame
    emails: pd.DataFrame
    analytics_data: pd.DataFrame
    plots_data: pd.DataFrame
    project_tasks: pd.DataFrame
    crm_data: pd.DataFrame
    directory_emails: pd.DataFrame

    @classmethod
    def from_csv_files(cls) -> "ToolState":
        return cls(
            calendar_events=_load_csv("calendar_events"),
            emails=_load_csv("emails"),
            analytics_data=_load_analytics_data(),
            plots_data=pd.DataFrame(columns=pd.Index(["file_path"])),
            project_tasks=_load_csv("project_tasks"),
            crm_data=_load_csv("crm_data"),
            directory_emails=_load_directory_emails(),
        )

    def reset(self) -> None:
        fresh = ToolState.from_csv_files()
        for f in fields(self):
            setattr(self, f.name, getattr(fresh, f.name))


_local = threading.local()


def get_state() -> "ToolState":
    state = getattr(_local, "tool_state", None)
    if state is None:
        _local.tool_state = ToolState.from_csv_files()
    return _local.tool_state


def reset_state() -> None:
    get_state().reset()
