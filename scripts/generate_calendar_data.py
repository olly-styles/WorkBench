import pandas as pd
import numpy as np
from tqdm import tqdm
from src.dataset_generation.calendar.data_generation_utils import create_calendar_event


event_names = pd.read_csv("data/raw/events.csv", header=None)
emails = pd.read_csv("data/raw/emails.csv", header=None)

events = pd.DataFrame(
    columns=["event_id", "event_name", "participant_email", "event_start", "event_end"]
)
for _ in tqdm(range(500)):
    event_id, event_name, email, event_start, event_end = create_calendar_event(
        event_names, emails, events
    )
    events.loc[len(events)] = [event_id, event_name, email, event_start, event_end]

events = events.sort_values(by="event_start").reset_index(drop=True)
events.to_csv("data/processed/calender_events.csv", index=False)
