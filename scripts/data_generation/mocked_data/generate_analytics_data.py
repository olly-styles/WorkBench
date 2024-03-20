import pandas as pd
import numpy as np
from datetime import timedelta, datetime

np.random.seed(42)


def generate_visitor_id(used_ids):
    visitor_id = str(np.random.randint(0, 9999)).zfill(4)
    while visitor_id in used_ids:
        visitor_id = generate_visitor_id(used_ids)
    return visitor_id


def generate_page_views():
    return int(np.random.exponential(5) + 1)


def generate_session_duration_seconds():
    return int(np.random.exponential(20))


def generate_traffic_source():
    return np.random.choice(["direct", "referral", "search engine", "social media"], p=[0.5, 0.1, 0.1, 0.3])


def generate_visit_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = np.random.randint(0, days_between_dates)
    return start_date + timedelta(days=random_number_of_days)


# Parameters for data generation
start_date = datetime(2023, 9, 1)
end_date = datetime(2023, 11, 30)
num_records = 1000

# Data structure to keep track of used visitor IDs per day
used_visitor_ids_per_day = {}

# Generate data
records = []
for _ in range(num_records):
    date_of_visit = generate_visit_date(start_date, end_date)
    used_ids = used_visitor_ids_per_day.get(date_of_visit, set())
    visitor_id = generate_visitor_id(used_ids)
    used_ids.add(visitor_id)
    used_visitor_ids_per_day[date_of_visit] = used_ids

    session_duration_seconds = generate_session_duration_seconds()
    page_views = generate_page_views()
    user_engaged = (session_duration_seconds > 10) & (page_views > 1)
    record = {
        "date_of_visit": date_of_visit,
        "visitor_id": visitor_id,
        "page_views": page_views,
        "session_duration_seconds": session_duration_seconds,
        "traffic_source": generate_traffic_source(),
        "user_engaged": user_engaged,
    }
    records.append(record)

analytics_data = pd.DataFrame(records)
analytics_data.to_csv("data/processed/analytics_data.csv", index=False)
