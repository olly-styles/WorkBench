import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import (
    generate_end_time,
    get_natural_language_date,
    generate_event_duration_minutes,
    format_event_duration,
    get_natural_language_time,
    get_random_future_date,
    get_first_free_slot,
)
from src.evals.utils import HARDCODED_CURRENT_TIME, generate_all_queries_and_answers
from src.tools import calendar

random.seed(42)

calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())
times = list(calendar_events["event_start"].str.split(" ").str[1].unique())
events = list(calendar_events["event_name"].unique())
emails = list(calendar_events["participant_email"].unique())
event_ids = list(calendar_events["event_id"].unique())


def first_event_logic():
    date = get_random_future_date(dates)
    natural_language_date = get_natural_language_date(date)
    first_event_id = calendar.search_events.func(time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")[0][
        "event_id"
    ]
    return {
        "natural_language_date": natural_language_date,
        "first_event_id": first_event_id,
    }


def last_event_name_change_logic():
    date = get_random_future_date(dates)
    natural_language_date = get_natural_language_date(date)
    last_event_id = calendar.search_events.func(time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")[-1][
        "event_id"
    ]
    new_event_name = random.choice(events)
    return {
        "natural_language_date": natural_language_date,
        "last_event_id": last_event_id,
        "event_name": new_event_name,
    }


def delay_first_meeting_logic():
    date = get_random_future_date(dates)
    natural_language_date = get_natural_language_date(date)
    duration_minutes = generate_event_duration_minutes()
    duration = format_event_duration(duration_minutes)
    events_on_date = calendar.search_events.func(query="", time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")
    name = random.choice(events_on_date)["participant_email"].split(".")[0]
    first_event_with_name = calendar.search_events.func(
        query=name, time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59"
    )[0]
    first_event_with_name_id = first_event_with_name["event_id"]
    new_start = generate_end_time(first_event_with_name["event_start"], duration)
    return {
        "natural_language_date": natural_language_date,
        "duration_minutes": duration_minutes,
        "duration": duration,
        "first_event_with_name_id": first_event_with_name_id,
        "new_start": new_start,
        "name": name,
    }


def cancel_event_logic():
    event_name = random.choice(events)
    events_with_name = calendar_events[calendar_events["event_name"] == event_name]
    next_event_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]
    # Keep trying until we find an event in the future
    while len(next_event_with_name) == 0:
        event_name = random.choice(events)
        events_with_name = calendar_events[calendar_events["event_name"] == event_name]
        next_event_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]

    next_event_with_name = next_event_with_name.iloc[0]

    return {"event_id": next_event_with_name["event_id"], "event_name": event_name}


def rename_event_logic():
    original_event = cancel_event_logic()
    new_event_name = random.choice(events)
    while new_event_name == original_event["event_name"]:
        new_event_name = random.choice(events)
    return {**original_event, "new_event_name": new_event_name}


def cancel_next_event_with_name_logic():
    participant = random.choice(emails)
    events_with_name = calendar_events[calendar_events["participant_email"] == participant]
    future_events_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]
    next_event_id = future_events_with_name.sort_values("event_start").iloc[0]["event_id"]
    name = participant.split(".")[0]
    return {"event_id": next_event_id, "name": name}


def check_last_meeting_with_name_schedule_30_tomorrow():
    participant = random.choice(emails)
    number_of_days = random.randint(1, 10)
    events_with_name = calendar_events[calendar_events["participant_email"] == participant]
    past_events_with_name = events_with_name[
        (events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME - pd.Timedelta(days=number_of_days)))
        & (events_with_name["event_start"] < str(HARDCODED_CURRENT_TIME))
    ]

    if len(past_events_with_name) != 0:
        return {
            "name": participant.split(".")[0],
            "duration": number_of_days,
            "answer": [],
        }

    tomorrow_date = str(HARDCODED_CURRENT_TIME + pd.Timedelta(days=1)).split(" ")[0]
    events_tomorrow = calendar_events[calendar_events["event_start"].str.split(" ").str[0] >= tomorrow_date]
    first_free_time = get_first_free_slot(events_tomorrow)
    answer = [
        f"""calendar.create_event.func(event_name='catch-up', participant_email='{participant}', event_start='{tomorrow_date} {first_free_time}', duration='30')"""
    ]

    return {
        "name": participant.split(".")[0],
        "duration": number_of_days,
        "answer": answer,
    }


def cancel_events_on_day_logic():
    next_7_days = [str(HARDCODED_CURRENT_TIME + pd.Timedelta(days=i)).split(" ")[0] for i in range(1, 8)]
    date = random.choice(next_7_days)

    next_day = pd.to_datetime(date).day_name()
    before_or_after = random.choice(["before", "after"])

    time = random.choice(times)
    natural_language_time = get_natural_language_time(time)

    events_on_date = calendar_events[calendar_events["event_start"].str.split(" ").str[0] == date]
    if before_or_after == "before":
        events_to_delete = events_on_date[events_on_date["event_start"].str.split(" ").str[1] <= time]
    else:
        events_to_delete = events_on_date[events_on_date["event_start"].str.split(" ").str[1] >= time]
    if len(events_to_delete) == 0:
        return {
            "next_day": next_day,
            "before_or_after": before_or_after,
            "time": time,
            "event_ids_to_delete": [],
            "answer": [],
            "natural_language_time": natural_language_time,
        }

    event_ids_to_delete = events_to_delete["event_id"].tolist()
    answer = [f"""calendar.delete_event.func(event_id='{event_id}')""" for event_id in event_ids_to_delete]
    return {
        "answer": answer,
        "next_day": next_day,
        "before_or_after": before_or_after,
        "natural_language_time": natural_language_time,
    }


def cancel_all_future_meetings_with_person_logic():
    participant = random.choice(emails)
    name = participant.split(".")[0]
    events_with_name = calendar_events[calendar_events["participant_email"] == participant]
    future_events_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]
    if len(future_events_with_name) == 0:
        return {"answer": [], "name": name}

    event_ids_to_delete = future_events_with_name["event_id"].tolist()
    answer = [f"""calendar.delete_event.func(event_id='{event_id}')""" for event_id in event_ids_to_delete]
    return {"answer": answer, "name": name}


def cancel_future_meetings_with_name_logic():
    event_name = random.choice(events)
    events_with_name = calendar_events[calendar_events["event_name"] == event_name]
    future_events_with_name = events_with_name[events_with_name["event_start"] > str(HARDCODED_CURRENT_TIME)]
    if len(future_events_with_name) == 0:
        return {"answer": [], "event_name": event_name}

    event_ids_to_delete = future_events_with_name["event_id"].tolist()
    answer = [f"""calendar.delete_event.func(event_id='{event_id}')""" for event_id in event_ids_to_delete]
    return {"answer": answer, "event_name": event_name.lower()}


def create_event_logic():
    duration_minutes = generate_event_duration_minutes()
    duration = format_event_duration(duration_minutes)
    email = random.choice(emails)
    event_name = random.choice(events)
    date = get_random_future_date(dates)
    natural_language_date = get_natural_language_date(date)
    time = random.choice(times)
    natural_language_time = get_natural_language_time(time)
    return {
        "duration_minutes": duration_minutes,
        "duration": duration,
        "email": email,
        "event_name": event_name,
        "date": date,
        "natural_language_date": natural_language_date,
        "time": time,
        "natural_language_time": natural_language_time,
    }


MULTI_ACTION_TEMPLATES = [
    {
        "query": "Cancel my first meeting on {natural_language_date}",
        "answer": ["""calendar.delete_event.func(event_id='{first_event_id}')"""],
        "logic": first_event_logic,
    },
    {
        "query": "Change the name of the last event on {natural_language_date} to {event_name}",
        "answer": [
            """calendar.update_event.func(event_id='{last_event_id}', field='event_name', new_value='{event_name}')"""
        ],
        "logic": last_event_name_change_logic,
    },
    {
        "query": "Push back my first meeting with {name} on {natural_language_date} by {duration}s",
        "answer": [
            """calendar.update_event.func(event_id='{first_event_with_name_id}', field='event_start', new_value='{new_start}')"""
        ],
        "logic": delay_first_meeting_logic,
    },
    {
        "query": "Cancel the next {event_name} meeting",
        "answer": ["""calendar.delete_event.func(event_id='{event_id}')"""],
        "logic": cancel_event_logic,
    },
    {
        "query": "Rename the next {event_name} meeting to {new_event_name}",
        "answer": [
            """calendar.update_event.func(event_id='{event_id}', field='event_name', new_value='{new_event_name}')"""
        ],
        "logic": rename_event_logic,
    },
    {
        "query": "Cancel my next meeting with {name}",
        "answer": ["""calendar.delete_event.func(event_id='{event_id}')"""],
        "logic": cancel_next_event_with_name_logic,
    },
    {
        "query": "If I haven't met with {name} in the last {duration} days, schedule a 30-minute meeting called 'catch-up' for my first free slot from tomorrow",
        "answer": "in_logic",
        "logic": check_last_meeting_with_name_schedule_30_tomorrow,
    },
    {
        "query": "Cancel my meetings on {next_day} {before_or_after} {natural_language_time}",
        "logic": cancel_events_on_day_logic,
        "answer": "in_logic",
    },
    {
        "query": "Cancel all future meetings with {name}",
        "answer": "in_logic",
        "logic": cancel_all_future_meetings_with_person_logic,
    },
    {
        "query": "Cancel future {event_name} meetings",
        "answer": "in_logic",
        "logic": cancel_future_meetings_with_name_logic,
    },
    {
        "query": "Create a {duration} event called {event_name} on {natural_language_date} at {time} with {email}",
        "answer": [
            """calendar.create_event.func(event_name='{event_name}', participant_email='{email}', event_start='{date} {time}', duration='{duration_minutes}')"""
        ],
        "logic": create_event_logic,
    },
]

# Generate a limited number of unique multi-action queries and answers
generated_queries_and_answers = []
max_queries_per_template = 3  # Limit the number of queries per template

if __name__ == "__main__":
    generated_queries_and_answers = generate_all_queries_and_answers(MULTI_ACTION_TEMPLATES, max_queries_per_template)

    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/calendar_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )
