import json
import random
from typing import Any

import pandas as pd

from src.data_generation.data_generation_utils import (
    HARDCODED_CURRENT_TIME,
    format_event_duration,
    generate_and_write_tasks_and_outcomes,
    generate_end_time,
    generate_event_duration_minutes,
    get_first_free_slot,
    get_first_name,
    get_natural_language_date,
    get_natural_language_time,
    get_random_future_date,
    random_choice_excluding,
)
from src.tools import calendar

calendar_events: Any = None
dates: Any = None
times: Any = None
events: Any = None
emails: Any = None


def load_data() -> None:
    global calendar_events, dates, times, events, emails
    if calendar_events is not None:
        return
    calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
    dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())
    times = list(calendar_events["event_start"].str.split(" ").str[1].unique())
    events = list(calendar_events["event_name"].unique())
    emails = list(calendar_events["participant_email"].unique())


def first_event_logic() -> dict:
    date = get_random_future_date(dates)
    natural_language_date = get_natural_language_date(date)
    first_event_id = json.loads(calendar.search_events(time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59"))[0][
        "event_id"
    ]
    answer = [f"""calendar.delete_event.func(event_id="{first_event_id}")"""]
    return {
        "natural_language_date": natural_language_date,
        "first_event_id": first_event_id,
        "outcome": answer,
    }


def last_event_name_change_logic() -> dict:
    date = get_random_future_date(dates)
    natural_language_date = get_natural_language_date(date)
    last_event_id = json.loads(calendar.search_events(time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59"))[-1][
        "event_id"
    ]
    new_event_name = random.choice(events)
    answer = [
        f"""calendar.update_event.func(event_id="{last_event_id}", field="event_name", new_value="{new_event_name}")"""
    ]
    return {
        "natural_language_date": natural_language_date,
        "last_event_id": last_event_id,
        "event_name": new_event_name,
        "outcome": answer,
    }


def delay_first_meeting_logic() -> dict:
    while True:
        date = get_random_future_date(dates)
        duration_minutes = generate_event_duration_minutes()
        events_on_date = json.loads(
            calendar.search_events(query="", time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")
        )
        name = get_first_name(random.choice(events_on_date)["participant_email"])
        first_event_with_name = json.loads(
            calendar.search_events(query=name, time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")
        )[0]
        event_start = pd.to_datetime(first_event_with_name["event_start"])
        latest_start = (
            event_start.normalize()
            + pd.Timedelta(hours=18)
            - pd.Timedelta(minutes=int(first_event_with_name["duration"]))
        )
        max_delay_minutes = int((latest_start - event_start).total_seconds() // 60)
        fitting_delays = [d for d in (30, 60, 90, 120) if d <= max_delay_minutes]
        if fitting_delays:
            duration_minutes = min(duration_minutes, max(fitting_delays))
            break
    duration = format_event_duration(duration_minutes)
    new_start = generate_end_time(first_event_with_name["event_start"], duration)
    natural_language_date = get_natural_language_date(date)
    first_event_with_name_id = first_event_with_name["event_id"]
    answer = [
        f"""calendar.update_event.func(event_id="{first_event_with_name_id}", field="event_start", new_value="{new_start}")"""
    ]
    return {
        "natural_language_date": natural_language_date,
        "duration_minutes": duration_minutes,
        "duration": duration,
        "first_event_with_name_id": first_event_with_name_id,
        "new_start": new_start,
        "name": name,
        "outcome": answer,
    }


def cancel_event_logic() -> dict:
    event_name = random.choice(events)
    events_with_name = calendar_events[calendar_events["event_name"] == event_name]
    next_event_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]
    # Keep trying until we find an event in the future
    while len(next_event_with_name) == 0:
        event_name = random.choice(events)
        events_with_name = calendar_events[calendar_events["event_name"] == event_name]
        next_event_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]

    next_event_with_name = next_event_with_name.iloc[0]
    answer = [f"""calendar.delete_event.func(event_id="{next_event_with_name["event_id"]}")"""]

    return {"event_id": next_event_with_name["event_id"], "event_name": event_name, "outcome": answer}


def rename_event_logic() -> dict:
    original_event = cancel_event_logic()
    new_event_name = random_choice_excluding(events, original_event["event_name"])

    answer = [
        f"""calendar.update_event.func(event_id="{original_event["event_id"]}", field="event_name", new_value="{new_event_name}")"""
    ]

    return {**original_event, "new_event_name": new_event_name, "outcome": answer}


def cancel_next_event_with_name_logic() -> dict:
    participant = random.choice(emails)
    name = get_first_name(participant)
    events_with_name = calendar_events[calendar_events["participant_email"] == participant]
    future_events_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]
    if len(future_events_with_name) == 0:
        return {"event_id": None, "name": name, "outcome": []}
    next_event_id = future_events_with_name.sort_values("event_start").iloc[0]["event_id"]
    answer = [f"""calendar.delete_event.func(event_id="{next_event_id}")"""]
    return {"event_id": next_event_id, "name": name, "outcome": answer}


def create_event_on_first_free_slot_tomorrow(event_name: str, participant: str, duration_minutes: int) -> str:
    tomorrow_date = str(HARDCODED_CURRENT_TIME + pd.Timedelta(days=1)).split(" ")[0]
    following_day = str(HARDCODED_CURRENT_TIME + pd.Timedelta(days=2)).split(" ")[0]
    events_on_date = calendar_events[
        (calendar_events["event_start"].str.split(" ").str[0] >= tomorrow_date)
        & (calendar_events["event_start"].str.split(" ").str[0] < following_day)
    ]
    first_free_time = get_first_free_slot(tomorrow_date, events_on_date, duration_minutes)
    return f"""calendar.create_event.func(event_name="{event_name}", participant_email="{participant}", event_start="{first_free_time}", duration="{duration_minutes}")"""


def check_last_meeting_with_name_schedule_30_tomorrow() -> dict:
    participant = random.choice(emails)
    number_of_days = random.randint(1, 10)
    events_with_name = calendar_events[calendar_events["participant_email"] == participant]
    past_events_with_name = events_with_name[
        (events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME - pd.Timedelta(days=number_of_days)))
        & (events_with_name["event_start"] < str(HARDCODED_CURRENT_TIME))
    ]

    if len(past_events_with_name) != 0:
        return {
            "name": get_first_name(participant),
            "duration": number_of_days,
            "outcome": [],
        }

    answer = [create_event_on_first_free_slot_tomorrow("catch-up", participant, 30)]
    return {
        "name": get_first_name(participant),
        "duration": number_of_days,
        "outcome": answer,
    }


def cancel_events_on_day_logic() -> dict:
    next_7_days = [str(HARDCODED_CURRENT_TIME + pd.Timedelta(days=i)).split(" ")[0] for i in range(1, 8)]
    date = random.choice(next_7_days)
    weekend_days = [5, 6]
    while pd.to_datetime(date).weekday() in weekend_days:
        date = random.choice(next_7_days)

    next_day = pd.to_datetime(date).day_name()
    before_or_after = random.choice(["before", "after"])

    time = random.choice(times)
    natural_language_time = get_natural_language_time(time)

    events_on_date = calendar_events[calendar_events["event_start"].str.split(" ").str[0] == date]

    if before_or_after == "before":
        events_to_delete = events_on_date[events_on_date["event_start"].str.split(" ").str[1] < time]
    else:
        events_to_delete = events_on_date[events_on_date["event_start"].str.split(" ").str[1] > time]
    if len(events_to_delete) == 0:
        return {
            "next_day": next_day,
            "before_or_after": before_or_after,
            "time": time,
            "event_ids_to_delete": [],
            "outcome": [],
            "natural_language_time": natural_language_time,
        }

    event_ids_to_delete = events_to_delete["event_id"].tolist()
    answer = [f"""calendar.delete_event.func(event_id="{event_id}")""" for event_id in event_ids_to_delete]
    return {
        "outcome": answer,
        "next_day": next_day,
        "before_or_after": before_or_after,
        "natural_language_time": natural_language_time,
    }


def cancel_all_future_meetings_with_person_logic() -> dict:
    participant = random.choice(emails)
    name = get_first_name(participant)
    events_with_name = calendar_events[calendar_events["participant_email"] == participant]
    future_events_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]
    if len(future_events_with_name) == 0:
        return {"outcome": [], "name": name}

    event_ids_to_delete = future_events_with_name["event_id"].tolist()
    answer = [f"""calendar.delete_event.func(event_id="{event_id}")""" for event_id in event_ids_to_delete]
    return {"outcome": answer, "name": name}


def cancel_future_meetings_with_name_logic() -> dict:
    event_name = random.choice(events)
    events_with_name = calendar_events[calendar_events["event_name"] == event_name]
    future_events_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]
    if len(future_events_with_name) == 0:
        return {"outcome": [], "event_name": event_name}

    event_ids_to_delete = future_events_with_name["event_id"].tolist()
    answer = [f"""calendar.delete_event.func(event_id="{event_id}")""" for event_id in event_ids_to_delete]
    return {"outcome": answer, "event_name": event_name.lower()}


def create_event_logic() -> dict:
    duration_minutes = generate_event_duration_minutes()
    duration = format_event_duration(duration_minutes)
    email = random.choice(emails)
    event_name = random.choice(events)
    date = get_random_future_date(dates)
    natural_language_date = get_natural_language_date(date)
    time = random.choice(times)
    natural_language_time = get_natural_language_time(time)
    answer = [
        f"""calendar.create_event.func(event_name="{event_name}", participant_email="{email}", event_start="{date} {time}", duration="{duration_minutes}")"""
    ]

    return {
        "duration_minutes": duration_minutes,
        "duration": duration,
        "email": email,
        "event_name": event_name,
        "date": date,
        "natural_language_date": natural_language_date,
        "time": time,
        "natural_language_time": natural_language_time,
        "outcome": answer,
        "name": get_first_name(email),
    }


CALENDAR_TEMPLATES = [
    {
        "task": "Cancel my first meeting on {natural_language_date}",
        "alternative_tasks": [
            "Delete my first meeting on {natural_language_date}",
            "can you cancel my first meeting on {natural_language_date}",
        ],
        "logic": first_event_logic,
    },
    {
        "task": "Change the name of the last event on {natural_language_date} to {event_name}",
        "alternative_tasks": [
            "Rename the last event on {natural_language_date} to {event_name}",
            "Can you change the name of the last event on {natural_language_date} to {event_name}",
        ],
        "logic": last_event_name_change_logic,
    },
    {
        "task": "Push back my first meeting with {name} on {natural_language_date} by {duration}s",
        "alternative_tasks": [
            "Delay my first meeting with {name} on {natural_language_date} by {duration}s",
            "please move my first meeting with {name} on {natural_language_date} by {duration}s",
        ],
        "logic": delay_first_meeting_logic,
    },
    {
        "task": "Cancel the next {event_name} meeting",
        "alternative_tasks": [
            "Delete the next {event_name} meeting",
            "Can you cancel the next {event_name} meeting",
        ],
        "logic": cancel_event_logic,
    },
    {
        "task": "Rename the next {event_name} meeting to {new_event_name}",
        "alternative_tasks": [
            "Change the name of the next {event_name} meeting to {new_event_name}",
            "can you rename the next {event_name} meeting to {new_event_name}",
        ],
        "logic": rename_event_logic,
    },
    {
        "task": "Cancel my next meeting with {name}",
        "alternative_tasks": [
            "{name} is off sick. Can you cancel my next meeting with them?",
            "I need to cancel my next meeting with {name}. Can you do that for me please?",
        ],
        "logic": cancel_next_event_with_name_logic,
    },
    {
        "task": "If I haven't met with {name} in the last {duration} days, schedule a 30-minute meeting called 'catch-up' for my first free slot from tomorrow",
        "alternative_tasks": [
            "I think I might need to catch up with {name}. Can you check if I've met with them in the last {duration} days? If not, schedule a 30-minute meeting for my first free slot from tomorrow",
            "have I met with {name} in the last {duration} days? If not, schedule a 30-minute meeting called 'catch-up' for my first free slot from tomorrow",
        ],
        "logic": check_last_meeting_with_name_schedule_30_tomorrow,
    },
    {
        "task": "Cancel my meetings on {next_day} {before_or_after} {natural_language_time}",
        "alternative_tasks": [
            "Delete my meetings on {next_day} {before_or_after} {natural_language_time}",
            "something came up. Can you cancel my meetings on {next_day} {before_or_after} {natural_language_time}?",
        ],
        "logic": cancel_events_on_day_logic,
    },
    {
        "task": "Cancel all future meetings with {name}",
        "alternative_tasks": [
            "{name} is leaving the company. Can you cancel all future meetings with them?",
            "I need to cancel all future meetings with {name}. Can you do that for me please?",
        ],
        "logic": cancel_all_future_meetings_with_person_logic,
    },
    {
        "task": "Cancel future {event_name} meetings",
        "alternative_tasks": [
            "Delete all the future {event_name} meetings",
            "We've decided we don't need any any more {event_name} meetings. Can you cancel all future ones?",
        ],
        "logic": cancel_future_meetings_with_name_logic,
    },
    {
        "task": "Create a {duration} event called {event_name} on {natural_language_date} at {natural_language_time} with {name}",
        "alternative_tasks": [
            "I haven't met with {name} in a while. Can you schedule a {duration} event called {event_name} on {natural_language_date} at {natural_language_time}?",
            "I need to catch up with {name}. can you schedule a {duration} event called {event_name} on {natural_language_date} at {natural_language_time}?",
        ],
        "logic": create_event_logic,
    },
]
for d in CALENDAR_TEMPLATES:
    d["domains"] = ["calendar"]


def generate_task_and_outcome() -> None:
    load_data()
    generate_and_write_tasks_and_outcomes(
        CALENDAR_TEMPLATES, "data/processed/tasks_and_outcomes/calendar_tasks_and_outcomes.csv"
    )


if __name__ == "__main__":
    generate_task_and_outcome()
