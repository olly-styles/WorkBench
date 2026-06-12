import csv
import random
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

HARDCODED_CURRENT_TIME = pd.to_datetime("2023-11-30T00:00:00")
calendar_days_in_future = 21  # end date is 21 december
calendar_days_in_past = 121  # start date is 1 august


def get_first_free_slot(
    date: str | pd.Timestamp, original_events_on_date: pd.DataFrame, duration_minutes: int
) -> pd.Timestamp | None:
    if original_events_on_date.empty:
        return pd.to_datetime(date).replace(hour=9, minute=0, second=0)

    events_df = original_events_on_date.copy()

    events_df["duration"] = pd.to_numeric(events_df["duration"])
    events_df["event_start"] = pd.to_datetime(events_df["event_start"])
    events_df["event_end"] = events_df["event_start"] + pd.to_timedelta(events_df["duration"], unit="m")

    # Define work hours
    work_start = events_df["event_start"].iloc[0].replace(hour=9, minute=0, second=0)
    work_end = events_df["event_start"].iloc[0].replace(hour=18, minute=0, second=0)

    # Sort events by start time
    events_df = events_df.sort_values(by="event_start")

    # Start checking from the beginning of the work day
    current_time = work_start
    for _, row in events_df.iterrows():
        if current_time + timedelta(minutes=duration_minutes) <= row["event_start"]:
            # Found a slot
            return current_time
        # Move to the end of the current meeting before checking the next slot
        current_time = max(current_time, row["event_end"])

    # Check if there's a slot at the end of the day
    if current_time + timedelta(minutes=duration_minutes) <= work_end:
        return current_time

    # If no slot found
    return None


def get_random_future_date(dates: list[str]) -> str:
    date = random.choice(dates)
    while date < str(HARDCODED_CURRENT_TIME).split(" ")[0]:
        date = random.choice(dates)
    return date


def get_random_future_datetime(dates: list[str]) -> pd.Timestamp:
    date = get_random_future_date(dates)
    return generate_datetime_between(
        start=pd.to_datetime(f"{date}T00:00:00"),
        end=pd.to_datetime(f"{date}T23:59:59"),
        nearest_30_minutes=True,
    )


def is_overlapping(new_start: pd.Timestamp, duration: int, existing_events: pd.DataFrame) -> bool:
    duration_delta = pd.Timedelta(duration, unit="m")
    existing_starts = existing_events["event_start"]
    existing_ends = existing_starts + existing_events["duration"].apply(lambda x: pd.Timedelta(x, unit="m"))
    new_end = new_start + duration_delta

    starts_during_existing = (new_start >= existing_starts) & (new_start < existing_ends)
    ends_during_existing = (new_end > existing_starts) & (new_end <= existing_ends)
    encompasses_existing = (new_start <= existing_starts) & (new_end >= existing_ends)

    overlap = starts_during_existing | ends_during_existing | encompasses_existing
    return overlap.any()


def event_on_the_same_day(new_start: pd.Timestamp, event_name: str, existing_events: pd.DataFrame) -> bool:
    new_start_date = pd.to_datetime(new_start).date()
    same_day = existing_events[
        existing_events["event_start"].apply(lambda x: pd.to_datetime(x).date()) == new_start_date
    ]
    return (same_day["event_name"] == event_name).any()


def create_calendar_event(
    event_names: pd.DataFrame, emails: pd.DataFrame, existing_events: pd.DataFrame
) -> tuple[str, str, str, pd.Timestamp, int]:
    while True:
        event_name = str(event_names.sample().iloc[0, 0])
        email = str(emails.sample().iloc[0, 0])
        event_start = generate_datetime_between(
            start=HARDCODED_CURRENT_TIME - pd.Timedelta(calendar_days_in_past, unit="d"),
            end=HARDCODED_CURRENT_TIME + pd.Timedelta(calendar_days_in_future, unit="d"),
        )
        # continue if the event start is on a weekend
        if event_start.weekday() in (5, 6):
            continue
        duration_minutes = generate_event_duration_minutes()
        event_id = str(len(existing_events)).zfill(8)

        # Check if the event time overlaps with an existing event time and that there is no event with the same name on the same day.
        # Note that this method is not very efficient, but it is good enough for this purpose. If you want to
        # generate a large dataset, you should use a more efficient method.
        if (not is_overlapping(event_start, duration_minutes, existing_events)) and (
            not event_on_the_same_day(event_start, event_name, existing_events)
        ):
            return event_id, event_name, email, event_start, duration_minutes


# generate_datetime_between option do nearest 30 minutes or not
def generate_datetime_between(start: pd.Timestamp, end: pd.Timestamp, nearest_30_minutes: bool = True) -> pd.Timestamp:
    month = np.random.randint(start.month, end.month + 1)
    min_day = start.day if month == start.month else 1
    max_day = end.day if month == end.month else 31
    # get max day accounting for months with different number of days
    max_day = min(max_day, 30) if month in [4, 6, 9, 11] else max_day
    max_day = min(max_day, 28) if month == 2 else max_day
    day = np.random.randint(min_day, max_day + 1)
    hour = np.random.randint(9, 16)
    if nearest_30_minutes:
        minute = np.random.choice([0, 30])
        seconds = "00"
    else:
        minute = np.random.randint(0, 60)
        seconds = str(np.random.randint(0, 60)).zfill(2)
    year = start.year if start.year == end.year else np.random.randint(start.year, end.year + 1)
    return pd.to_datetime(f"{year}-{month}-{day}T{hour}:{minute}:{seconds}")


def get_natural_language_date(str_date: str) -> str:
    """Transforms a datetime string into just natural language date.

    Example: 2023-01-01 -> January 1
    """
    date = pd.to_datetime(str_date)
    return date.strftime("%B %d").lstrip("0").replace(" 0", " ")


def generate_event_duration_minutes() -> int:
    return int(np.random.choice([30, 60, 90, 120]))


def format_event_duration(duration_minutes: int) -> str:
    """Format the duration of an event in natural language.

    Examples: 180 -> 3 hour, 30 -> 30 minute
    """
    if duration_minutes < 60:
        return f"{duration_minutes} minute"
    duration_hours = duration_minutes / 60
    if duration_hours == int(duration_hours):
        duration_hours = int(duration_hours)
    return f"{duration_hours} hour"


def generate_end_time(start_time: str, duration: str) -> str:
    """
    Generate the end time of an event given the start time and duration.
    """
    return (pd.to_datetime(start_time) + pd.Timedelta(duration)).strftime("%Y-%m-%d %H:%M:%S")


def create_email(
    existing_emails: pd.DataFrame, email_content: pd.DataFrame, max_attempts: int = 1000
) -> tuple[str, str, str, pd.Timestamp, str]:
    email_id = str(len(existing_emails)).zfill(8)
    existing_dates = existing_emails["sent_datetime"].apply(lambda x: x.strftime("%Y-%m-%d"))
    for _ in range(max_attempts):
        email_content_pairs = email_content.sample().iloc[0].to_dict()
        recipient = email_content_pairs["Sender"]
        subject = email_content_pairs["Subject"]
        body = email_content_pairs["Content"]
        sent_datetime = generate_datetime_between(
            start=pd.to_datetime("2023-10-01T00:00:00"),
            end=HARDCODED_CURRENT_TIME,
            nearest_30_minutes=False,
        )
        sent_date = sent_datetime.strftime("%Y-%m-%d")
        # skip if there is already an email with the same subject on the same day
        if subject in existing_emails[existing_dates == sent_date]["subject"].values:
            continue

        return email_id, recipient, subject, sent_datetime, body
    raise ValueError(f"Failed to generate unique email after {max_attempts} attempts")


def get_natural_language_time(str_time: str) -> str:
    """Transforms a datetime string into just natural language time.

    For example: 09:30:00 -> 9:30am, 13:00:00 -> 1
    """
    dt = datetime.strptime(str_time, "%H:%M:%S")
    if dt.minute == 0:
        return dt.strftime("%-I")
    return dt.strftime("%-I:%M")


def get_first_name(email: str) -> str:
    return email.split("@")[0].split(".")[0]


def random_choice_excluding(collection: Sequence[Any], exclude: Any) -> Any:
    choice = random.choice(collection)
    while choice == exclude:
        choice = random.choice(collection)
    return choice


def write_task_outcome_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False, quoting=csv.QUOTE_ALL)


def generate_task_and_outcome(template: dict[str, Any]) -> dict[str, Any]:
    """Generates task and outcome from template."""
    logic = template["logic"]()
    possible_tasks = [template["task"]] + template["alternative_tasks"]
    task_template = random.choice(possible_tasks)
    return {
        "task": task_template.format(**logic),
        "outcome": logic["outcome"],
        "base_template": template["task"],
        "chosen_template": task_template,
        "domains": template["domains"],
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


def generate_and_write_tasks_and_outcomes(
    templates: list[dict[str, Any]], output_path: str, max_tasks_per_template: int = 10
) -> None:
    """Seed the RNGs, generate tasks from ``templates``, and write them to ``output_path``."""
    np.random.seed(42)
    random.seed(42)
    generated_tasks_and_outcomes = generate_all_tasks_and_outcomes(templates, max_tasks_per_template)
    write_task_outcome_csv(pd.DataFrame(generated_tasks_and_outcomes), output_path)
