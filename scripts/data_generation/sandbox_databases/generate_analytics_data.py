import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

SEED_DATA_DIR = Path(__file__).parent.parent / "seed_data"
ANALYTICS_SEED = json.loads((SEED_DATA_DIR / "analytics.json").read_text())


def generate_visitor_id(used_ids: set[str], max_attempts: int = 1000) -> str:
    for _ in range(max_attempts):
        visitor_id = str(np.random.randint(0, 9999)).zfill(4)
        if visitor_id not in used_ids:
            return visitor_id
    raise ValueError(f"Failed to generate unique visitor ID after {max_attempts} attempts")


def generate_page_views() -> int:
    return int(np.random.exponential(5) + 1)


def generate_session_duration_seconds() -> int:
    return int(np.random.exponential(20))


def generate_traffic_source() -> str:
    return np.random.choice(ANALYTICS_SEED["traffic_sources"], p=ANALYTICS_SEED["traffic_source_probabilities"])


def generate_visit_date(start_date: datetime, end_date: datetime) -> datetime:
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = np.random.randint(0, days_between_dates)
    return start_date + timedelta(days=random_number_of_days)


def generate_data() -> None:
    random.seed(42)
    np.random.seed(42)
    # Parameters for data generation
    start_date = datetime(2023, 9, 1)
    end_date = datetime(2023, 11, 30)
    num_records = 1000

    # Data structure to keep track of used visitor IDs per day
    used_visitor_ids_per_day = {}

    records = []
    for _ in tqdm(range(num_records)):
        date_of_visit = generate_visit_date(start_date, end_date)
        used_ids = used_visitor_ids_per_day.get(date_of_visit, set())
        visitor_id = generate_visitor_id(used_ids)
        used_ids.add(visitor_id)
        used_visitor_ids_per_day[date_of_visit] = used_ids

        session_duration_seconds = generate_session_duration_seconds()
        page_views = generate_page_views()
        user_engaged = (session_duration_seconds > 10) and (page_views > 1)
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


if __name__ == "__main__":
    generate_data()
