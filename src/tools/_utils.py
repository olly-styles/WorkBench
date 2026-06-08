import json

import pandas as pd

DEFAULT_SEARCH_RESULT_LIMIT = 5


def normalize_email(email: str) -> str:
    return email.lower()


def validate_email(email: str) -> bool:
    return "@" in email and "." in email


def filter_by_date_range(df: pd.DataFrame, date_col: str, time_min: str | None, time_max: str | None) -> pd.DataFrame:
    data = df[df[date_col] >= time_min].copy() if time_min else df.copy()
    if time_max:
        data = data[data[date_col] <= time_max]
    return data


def get_record_field(
    df: pd.DataFrame,
    id_col: str,
    record_id: str | None,
    field: str | None,
    record_name: str,
) -> str:
    if not record_id:
        return f"{record_name} ID not provided."
    if not field:
        return "Field not provided."
    record = df[df[id_col] == record_id].to_dict(orient="records")
    if not record:
        return f"{record_name} not found."
    if field in record[0]:
        return json.dumps({field: record[0][field]})
    return "Field not found."


def generate_next_id(df: pd.DataFrame, id_col: str) -> str:
    if df.empty:
        return "0".zfill(8)
    return str(int(df[id_col].max()) + 1).zfill(8)


def delete_record(df: pd.DataFrame, id_col: str, record_id: str | None, record_name: str) -> tuple[pd.DataFrame, str]:
    if not record_id:
        return df, f"{record_name} ID not provided."
    if record_id in df[id_col].values:
        return df[df[id_col] != record_id], f"{record_name} deleted successfully."
    return df, f"{record_name} not found."
