import pandas as pd
import numpy as np
from tqdm import tqdm
from src.data_generation.calendar.data_generation_utils import create_calendar_event


event_names = pd.read_csv("data/raw/events.csv", header=None)
emails = pd.read_csv("data/raw/email_addresses.csv", header=None)

events = pd.DataFrame(
    columns=["event_id", "event_name", "participant_email", "event_start", "duration"]
)
for _ in tqdm(range(500)):
    event_id, event_name, email, event_start, duration = create_calendar_event(
        event_names, emails, events
    )
    events.loc[len(events)] = [event_id, event_name, email, event_start, duration]

events = events.sort_values(by="event_start").reset_index(drop=True)
events.to_csv("data/processed/calendar_events.csv", index=False)
