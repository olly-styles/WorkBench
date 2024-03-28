import pandas as pd
import random
import csv
import sys
import os
import numpy as np

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import (
    HARDCODED_CURRENT_TIME,
    format_event_duration,
    generate_event_duration_minutes,
    get_natural_language_date,
    get_natural_language_time,
    get_random_future_datetime,
)
from src.tools import calendar
from src.evals.utils import generate_all_queries_and_answers
from scripts.data_generation.query_answer_generation.generate_calendar_query_and_answer import (
    create_event_on_first_free_slot_tomorrow,
)
from scripts.data_generation.query_answer_generation.generate_analytics_query_and_answer import (
    metric_more_or_less_plot_logic,
    relative_growth_two_plots_logic,
)
from scripts.data_generation.query_answer_generation.generate_project_management_query_and_answer import (
    get_new_task_string,
    get_random_task_dict,
)
from scripts.data_generation.query_answer_generation.generate_customer_relationship_manager_query_and_answer import (
    get_random_dict as get_crm_dict,
    CRM_DATA,
)

random.seed(42)

emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())
times = list(calendar_events["event_start"].str.split(" ").str[1].unique())
project_tasks = pd.read_csv("data/processed/project_tasks.csv", dtype=str)


def get_base_email_dict():
    email_index = random.randint(0, len(emails_data) - 1)
    natural_language_email_date = get_natural_language_date(emails_data["sent_datetime"][email_index].split(" ")[0])
    subject = emails_data["subject"][email_index]
    sender = emails_data["sender/recipient"][email_index]
    return {
        "natural_language_email_date": natural_language_email_date,
        "subject": subject,
        "sender": sender,
        "sender_name": sender.split(".")[0],
    }


def get_base_event_dict():
    duration_minutes = generate_event_duration_minutes()
    natural_language_duration = format_event_duration(duration_minutes)
    event_datetime = str(get_random_future_datetime(dates))
    event_date = event_datetime.split(" ")[0]
    natural_language_event_date = get_natural_language_date(event_date)
    event_time = event_datetime.split(" ")[1]
    natural_language_event_time = get_natural_language_time(event_time)
    return {
        "natural_language_duration": natural_language_duration,
        "event_datetime": event_datetime,
        "event_date": event_date,
        "natural_language_event_date": natural_language_event_date,
        "event_time": event_time,
        "natural_language_time": natural_language_event_time,
        "duration": duration_minutes,
    }


def new_event_string(event_name, email, event_datetime, duration):
    return f"""calendar.create_event.func(event_name="{event_name}", participant_email="{email}", event_start="{event_datetime}", duration="{duration}")"""


def new_email_string(email, subject, body):
    return f"""email.send_email.func(recipient="{email}", subject="{subject}", body="{body}")"""


def get_first_event_id_on_date(date):
    events = calendar.search_events.func(time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")
    if events == "No events found.":
        return events
    return events[0]["event_id"]


def get_next_friday_date():
    return str(HARDCODED_CURRENT_TIME.date() + pd.Timedelta(7 + (4 - HARDCODED_CURRENT_TIME.dayofweek), "D"))


def book_meeting_if_no_customer_contact_logic():
    """If we haven't spoke to {current_customer_name} in the past fortnight book a 30-minute meeting with whoever is assigned to them
    called 'Update on {current_customer_name}' at the first time I'm free tomorrow"""
    crm_dict = get_crm_dict()
    customer_data = CRM_DATA[CRM_DATA["customer_name"] == crm_dict["current_customer_name"]]
    crm_dict["assigned_to_email"] = customer_data["assigned_to_email"].values[
        0
    ]  # Override the assignee email with the one from the CRM
    last_contact_date = pd.to_datetime(customer_data["last_contact_date"].values[0])
    if HARDCODED_CURRENT_TIME - last_contact_date > pd.Timedelta(14, "D"):
        event_name = f"Update on {crm_dict['current_customer_name']}"
        create_event_action = create_event_on_first_free_slot_tomorrow(event_name, crm_dict["assigned_to_email"], 30)
        return {**crm_dict, "answer": [create_event_action]}
    return {**crm_dict, "answer": []}


def find_person_with_fewest_overdue_tasks():
    overdue_tasks = project_tasks[
        (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME.date()))
        & (project_tasks["list_name"].isin(["Completed"]) == False)
    ]
    return overdue_tasks["assigned_to_email"].value_counts().idxmin()


def add_new_customer_fewest_overdue_tasks_logic():
    """Add {new_customer_name} as a new lead in the crm and assign them to the person with the fewest overdue tasks"""
    crm_dict = get_crm_dict()
    person_with_fewest_overdue_tasks = find_person_with_fewest_overdue_tasks()
    answer = [
        f"""customer_relationship_manager.add_customer.func(customer_name="{crm_dict['new_customer_name']}", assigned_to_email="{person_with_fewest_overdue_tasks}", status="Lead")"""
    ]
    return {**crm_dict, "answer": answer}


def find_email_schedule_event_sender_logic():
    email_dict = get_base_email_dict()
    event_dict = get_base_event_dict()
    answer = [
        new_event_string(
            email_dict["subject"], email_dict["sender"], event_dict["event_datetime"], event_dict["duration"]
        )
    ]
    return {**email_dict, **event_dict, "answer": answer}


def find_event_send_email_logic():
    event_dict = get_base_event_dict()
    first_event_id = get_first_event_id_on_date(event_dict["event_date"])
    if first_event_id == "No events found.":
        return {**event_dict, "answer": []}
    event_dict["participant"] = calendar_events.set_index("event_id").loc[first_event_id, "participant_email"]
    event_dict["event_name"] = calendar_events.set_index("event_id").loc[first_event_id, "event_name"]
    answer = [new_email_string(event_dict["participant"], event_dict["event_name"], "Remember to attend this event.")]
    return {**event_dict, "answer": answer}


def schedule_event_if_no_emails_logic():
    """If {sender_name} hasn't sent me any emails in the past {days} days, schedule a 30 minute meeting with them for {day_of_week} at {natural_language_time} called 'Catch up with {sender_name}'""",
    email_dict = get_base_email_dict()
    event_dict = get_base_event_dict()
    days_since_email = random.randint(2, 4)
    dates_up_to_6_days_in_the_future = [str(HARDCODED_CURRENT_TIME.date() + pd.Timedelta(days=i)) for i in range(1, 7)]
    no_weekend_dates = [date for date in dates_up_to_6_days_in_the_future if pd.to_datetime(date).dayofweek < 5]
    event_dict["event_date"] = random.choice(no_weekend_dates)
    event_datetime = f"{event_dict['event_date']} {event_dict['event_time']}"
    day_of_week = pd.to_datetime(event_dict["event_date"]).day_name()
    answer = []
    if emails_data[
        (emails_data["sender/recipient"] == email_dict["sender"])
        & (emails_data["sent_datetime"] > str(HARDCODED_CURRENT_TIME - pd.Timedelta(days=days_since_email)))
    ].empty:
        answer.append(
            new_event_string(
                f"Catch up with {email_dict['sender_name']}",
                email_dict["sender"],
                event_datetime,
                30,
            )
        )

    return {**email_dict, **event_dict, "days": days_since_email, "answer": answer, "day_of_week": day_of_week}


def send_email_if_no_past_meetings_logic():
    """If I haven't met with {name} in the past {days} days, send them an email titled 'Catch up soon?' saying 'We haven't caught up in a while - can you send some availability over next week?'"""
    email = random.choice(calendar_events["participant_email"].unique())
    name = email.split(".")[0]
    threshold_days_since_last_meeting = random.choice([2, 10])
    past_events = calendar_events[
        (calendar_events["participant_email"] == email) & (calendar_events["event_start"] < str(HARDCODED_CURRENT_TIME))
    ]
    if not len(past_events):
        answer = [
            new_email_string(
                email,
                "Catch up soon?",
                f"We haven't caught up in a while - can you send some availability over next week?",
            )
        ]
    last_event_date = past_events.sort_values("event_start", ascending=False).iloc[0]["event_start"].split(" ")[0]
    threshold_date = str((HARDCODED_CURRENT_TIME - pd.Timedelta(days=threshold_days_since_last_meeting)).date())
    if last_event_date < threshold_date:
        answer = [
            new_email_string(
                email,
                "Catch up soon?",
                f"We haven't caught up in a while - can you send some availability over next week?",
            )
        ]
    else:
        answer = []
    return {
        "name": name,
        "days": threshold_days_since_last_meeting,
        "last_event_date": last_event_date,
        "answer": answer,
    }


def send_email_if_no_future_meetings_logic():
    """If I don't have any meetings scheduled with {name} in the next {days} days, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'""",
    base_dict = get_base_email_dict()
    next_event_date = None
    threshold_days_until_next_meeting = random.randint(2, 4)
    future_events = calendar_events[
        (calendar_events["participant_email"] == base_dict["sender"])
        & (calendar_events["event_start"] > str(HARDCODED_CURRENT_TIME))
    ]
    answer = []
    if not len(future_events):
        answer = [
            new_email_string(
                base_dict["sender"],
                "Catch up soon?",
                "We have not caught up in a while - can you send some availability over next week?",
            )
        ]
    else:
        next_event_date = future_events.sort_values("event_start", ascending=True).iloc[0]["event_start"].split(" ")[0]
        threshold_date = str((HARDCODED_CURRENT_TIME + pd.Timedelta(days=threshold_days_until_next_meeting)).date())
        if next_event_date > threshold_date:
            answer = [
                new_email_string(
                    base_dict["sender"],
                    "Catch up soon?",
                    "We have not caught up in a while - can you send some availability over next week?",
                )
            ]
        else:
            answer = []
    return {
        "name": base_dict["sender_name"],
        "days": threshold_days_until_next_meeting,
        "next_event_date": next_event_date,
        "answer": answer,
    }


def overdue_tasks_base_dict():
    email = random.choice(project_tasks["assigned_to_email"].unique())
    name = email.split(".")[0]
    overdue_tasks = project_tasks[
        (project_tasks["assigned_to_email"] == email)
        & (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME.date()))
        & (project_tasks["list_name"].isin(["Completed"]) == False)
    ]
    return {"email": email, "name": name, "overdue_tasks": overdue_tasks}


def send_email_for_overdue_tasks_logic():
    """If {name} has any overdue tasks, send them an email titled 'Overdue tasks' saying 'You have a few overdue tasks - can you update me on them?'.
    Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"""
    base_dict = overdue_tasks_base_dict()
    if len(base_dict["overdue_tasks"]):
        answer = [
            (
                new_email_string(
                    base_dict["email"], "Overdue tasks", "You have a few overdue tasks - can you update me on them?"
                )
            )
        ]
    else:
        answer = [
            (
                new_email_string(
                    base_dict["email"], "Good work this sprint", "Nice work keeping on top of your tasks this sprint!"
                )
            )
        ]
    return {**base_dict, "answer": answer}


def find_person_with_most_completed_tasks(board):
    return (
        project_tasks[(project_tasks["list_name"] == "Completed") & (project_tasks["board"] == board)][
            "assigned_to_email"
        ]
        .value_counts()
        .idxmax()
    )


def book_meeting_with_overdue_tasks_logic():
    """Book a half-hour meeting with {name} called 'Catch up on overdue tasks' at the earliest time I'm free tomorrow if they have any overdue tasks"""
    base_dict = overdue_tasks_base_dict()
    answer = []
    if len(base_dict["overdue_tasks"]):
        event_name = "Catch up on overdue tasks"
        create_event_action = create_event_on_first_free_slot_tomorrow(event_name, base_dict["email"], 30)
        answer.append(create_event_action)
    return {**base_dict, "answer": answer}


def send_email_if_metric_more_or_less_than_threshold_logic():
    """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}
    send an email to {email} titled 'Update on {metric}' saying 'I noticed {metric} was {more_or_less} than {threshold} - can you update me?'
    """
    metric_dict = metric_more_or_less_plot_logic()
    email_dict = get_base_email_dict()
    if len(metric_dict["answer"]):  # If the metric was more or less than the threshold there will be a plot here
        metric_dict["answer"] = [
            new_email_string(
                email_dict["sender"],
                f"Update on {metric_dict['natural_language_metric']}",
                f"I noticed {metric_dict['natural_language_metric']} was {metric_dict['more_or_less']} than {metric_dict['threshold']} - can you update me?",
            )
        ]
    return {**metric_dict, "sender": email_dict["sender"]}


def schedule_event_if_metric_more_or_less_than_threshold_logic():
    """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}
    schedule a half-hour meeting called 'Discuss {natural_language_metric}' with {sender_name} at the earliest time I'm free tomorrow
    """
    metric_dict = metric_more_or_less_plot_logic()
    event_dict = get_base_event_dict()
    email_dict = get_base_email_dict()
    if len(metric_dict["answer"]):  # If the metric was more or less than the threshold there will be a plot here
        event_name = f"Discuss {metric_dict['natural_language_metric']}"
        create_event_action = create_event_on_first_free_slot_tomorrow(event_name, email_dict["sender"], 30)
        metric_dict["answer"] = [create_event_action]
    return {**metric_dict, **event_dict, **email_dict}


def make_task_if_metric_more_or_less_than_threshold_logic():
    """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}
    make a task 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday"""
    metric_dict = metric_more_or_less_plot_logic()
    task_dict = get_random_task_dict()
    next_friday_date = get_next_friday_date()
    if len(metric_dict["answer"]):  # If the metric was more or less than the threshold there will be a plot here
        task_dict["task_name"] = f"Improve {metric_dict['natural_language_metric']}"
        metric_dict["answer"] = [
            get_new_task_string(task_dict["task_name"], task_dict["email"], "Front end", next_friday_date)
        ]
    return {**metric_dict, **task_dict}


def make_task_if_relative_growth_logic():
    """Can you check the % growth of {natural_language_metric} since {day_of_week}? If it grew by more than {natural_language_metric_2}
    make a backlog task called 'Improve {natural_language_metric_2}' for {name} on the front-end board with a deadline of next Friday
    """
    metric_dict = relative_growth_two_plots_logic()
    task_dict = get_random_task_dict()
    next_friday_date = get_next_friday_date()
    if len(metric_dict["answer"]):  # If the metric was more or less than the threshold there will be a plot here
        task_dict["task_name"] = f"Improve {metric_dict['natural_language_metric_2']}"
        metric_dict["answer"] = [
            get_new_task_string(task_dict["task_name"], task_dict["email"], "Front end", next_friday_date)
        ]
    return {**metric_dict, **task_dict}


def book_event_send_email_if_overdue_tasks_logic():
    """If {name} has any overdue tasks, book a half hour meeting with them called 'Catch up on overdue tasks' at the earliest time I'm free tomorrow and
    send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - lets catch up tomorrow.
    Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"""
    base_dict = overdue_tasks_base_dict()
    answer = []
    if len(base_dict["overdue_tasks"]):
        event_name = "Catch up on overdue tasks"
        create_event_action = create_event_on_first_free_slot_tomorrow(event_name, base_dict["email"], 30)
        email_action = new_email_string(
            base_dict["email"],
            "Discuss overdue tasks",
            "I noticed you have a few overdue tasks - let's catch up tomorrow.",
        )
        answer = [create_event_action, email_action]
    else:
        answer = [
            new_email_string(
                base_dict["email"], "Good work this sprint", "Nice work keeping on top of your tasks this sprint!"
            )
        ]
    return {**base_dict, "answer": answer}


def make_task_person_most_completed_if_metric_vs_threshold_logic():
    """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}
    make a backlog task called 'Improve {natural_language_metric}' on the front-end board with a deadline of next Friday
    for the person with the most completed front end tasks"""
    metric_dict = metric_more_or_less_plot_logic()
    task_dict = get_random_task_dict()
    next_friday_date = get_next_friday_date()
    if len(metric_dict["answer"]):  # If the metric was more or less than the threshold there will be a plot here
        task_dict["email"] = find_person_with_most_completed_tasks("Front end")
        task_dict["task_name"] = f"Improve {metric_dict['natural_language_metric']}"
        metric_dict["answer"] = [
            get_new_task_string(task_dict["task_name"], task_dict["email"], "Front end", next_friday_date)
        ]
    return {**metric_dict, **task_dict}


def make_task_if_relative_growth_logic():
    """Check the % growth of {natural_language_metric} since {day_of_week} and if was more than {natural_language_metric_2}
    make a backlog task called 'Improve {natural_language_metric_2}' for {name} on the front-end board with a deadline of next Friday
    """
    metric_dict = relative_growth_two_plots_logic()
    task_dict = get_random_task_dict()
    next_friday_date = get_next_friday_date()
    if len(metric_dict["answer"]):  # If the metric grew by more than the threshold there will be a plot here
        task_dict["task_name"] = f"Improve {metric_dict['natural_language_metric_2']}"
        metric_dict["answer"] = [
            get_new_task_string(task_dict["task_name"], task_dict["email"], "Front end", next_friday_date)
        ]
    return {**metric_dict, **task_dict}


def make_task_or_send_email_if_metric_more_or_less_than_threshold_logic():
    """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}
    make a task 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday
    other send them an email titled '{natural_language_metric}' saying 'I noticed {natural_language_metric} has been stable, nice work!'
    """
    metric_dict = metric_more_or_less_plot_logic()
    task_dict = get_random_task_dict()
    next_friday_date = get_next_friday_date()
    if len(metric_dict["answer"]):  # If the metric was more or less than the threshold there will be a plot here
        task_dict["task_name"] = f"Improve {metric_dict['natural_language_metric']}"
        metric_dict["answer"] = [
            get_new_task_string(f'{task_dict["task_name"]}', task_dict["email"], "Front end", next_friday_date)
        ]
    else:
        metric_dict["answer"] = [
            new_email_string(
                task_dict["email"],
                f'Recent {metric_dict["natural_language_metric"]}',
                f"I noticed {metric_dict['natural_language_metric']} has been stable, nice work!",
            )
        ]
    return {**metric_dict, **task_dict}


def make_task_and_book_meeting_if_relative_growth_logic():
    """Check the % growth of {natural_language_metric} since {day_of_week} and if was more than {natural_language_metric_2}
    make a backlog task called 'Improve {natural_language_metric_2}' for {name} on the front-end board with a deadline of next Friday
    and schedule a half-hour meeting called 'Discuss {natural_language_metric}' with {name} at the first time I can do tomorrow
    """
    metric_dict = relative_growth_two_plots_logic()
    task_dict = get_random_task_dict()
    event_dict = get_base_event_dict()
    next_friday_date = get_next_friday_date()
    if len(metric_dict["answer"]):  # If the metric grew by more than the threshold there will be a plot here
        task_dict["task_name"] = f"Improve {metric_dict['natural_language_metric_2']}"
        metric_dict["answer"] = [
            get_new_task_string(task_dict["task_name"], task_dict["email"], "Front end", next_friday_date)
        ]
        event_name = f"Discuss {metric_dict['natural_language_metric']}"
        create_event_action = create_event_on_first_free_slot_tomorrow(event_name, task_dict["email"], 30)
        metric_dict["answer"].append(create_event_action)
    return {**metric_dict, **task_dict, **event_dict}


def delete_all_customers_if_metric_more_than_threshold_logic():
    """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}
    delete all {assigned_to_first_name}'s leads in the CRM"""
    metric_dict = metric_more_or_less_plot_logic()
    crm_dict = get_crm_dict()
    if len(metric_dict["answer"]):
        leads_to_delete = CRM_DATA[
            (CRM_DATA["assigned_to_email"] == crm_dict["assigned_to_email"]) & (CRM_DATA["status"] == "Lead")
        ]
        answer = [
            f"""customer_relationship_manager.delete_customer.func(customer_id="{lead_id}")"""
            for lead_id in leads_to_delete["customer_id"]
        ]
        metric_dict["answer"] = answer
    return {**metric_dict, **crm_dict}


def delete_all_customers_send_email_if_metric_more_than_threshold_logic():
    """If {natural_language_metric} was more than {threshold} at any time since {natural_language_date}
    delete all {assigned_to_name}'s leads in the CRM and send them an email titled 'Reprioritising'
    saying ''{natural_language_metric} looks good, so we no longer need you finding new leads'
    If not say in the email 'We need you to improve {natural_language_metric} - TBD.'"""
    metric_dict = metric_more_or_less_plot_logic()
    crm_dict = get_crm_dict()
    if len(metric_dict["answer"]):
        leads_to_delete = CRM_DATA[
            (CRM_DATA["assigned_to_email"] == crm_dict["assigned_to_email"]) & (CRM_DATA["status"] == "Lead")
        ]
        answer = [
            f"""customer_relationship_manager.delete_customer.func(customer_id="{lead_id}")"""
            for lead_id in leads_to_delete["customer_id"]
        ]
        answer.append(
            new_email_string(
                crm_dict["assigned_to_email"],
                "Reprioritising",
                f"{metric_dict['natural_language_metric']} looks good, so we no longer need you finding new leads",
            )
        )
        metric_dict["answer"] = answer
    else:
        metric_dict["answer"] = [
            new_email_string(
                crm_dict["assigned_to_email"],
                "Reprioritising",
                f"We need you to improve {metric_dict['natural_language_metric']} - TBD.",
            )
        ]
    return {**metric_dict, **crm_dict}


def make_task_book_meeting_or_send_email_if_metric_more_or_less_than_threshold_logic():
    """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}
    make a backlog task called 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday
    and book a half-hour meeting with {name} called 'Discuss {natural_language_metric}' at the earliest time I'm free tomorrow
    otherwise send them an email titled '{natural_language_metric}' saying 'I noticed {natural_language_metric} has been stable, nice work!'
    """
    metric_dict = make_task_or_send_email_if_metric_more_or_less_than_threshold_logic()
    if metric_dict["more_or_less"] in metric_dict["metric_vs_threshold"]:  # condition matches
        event_name = f"Discuss {metric_dict['natural_language_metric']}"
        create_event_action = create_event_on_first_free_slot_tomorrow(event_name, metric_dict["email"], 30)
        metric_dict["answer"].append(create_event_action)
    return metric_dict


def make_task_book_meeting_or_send_email_new_leads_if_metric_more_or_less_than_threshold_logic():
    """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}
    make a backlog task called 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday
    and book a half-hour meeting with {name} called 'Discuss {natural_language_metric}' at the earliest time I'm free tomorrow
    otherwise send them an email titled 'New leads for you' saying '{natural_language_metric} looks good, so there are new leads for you'
    and then give them all {assigned_to_first_name}'s leads in the CRM"""
    metric_dict = make_task_book_meeting_or_send_email_if_metric_more_or_less_than_threshold_logic()
    crm_dict = get_crm_dict()
    if metric_dict["more_or_less"] in metric_dict["metric_vs_threshold"]:  # condition matches
        return {**metric_dict, **crm_dict}
    else:
        leads_to_reassign = CRM_DATA[
            (CRM_DATA["assigned_to_email"] == crm_dict["assigned_to_email"]) & (CRM_DATA["status"] == "Lead")
        ]
        answer = [
            f"""customer_relationship_manager.update_customer.func(customer_id="{lead_id}", field="assigned_to_email", new_value="{metric_dict['email']}")"""
            for lead_id in leads_to_reassign["customer_id"]
        ]
        new_email = new_email_string(
            metric_dict["email"],
            "New leads for you",
            f"{metric_dict['natural_language_metric']} looks good, so there are new leads for you",
        )
        answer.append(new_email)
        metric_dict["answer"] = answer
        return {**metric_dict, **crm_dict}


MULTI_DOMAIN_TEMPLATES = [
    # CRM + calendar
    {
        "query": (
            "If we haven't spoke to {current_customer_name} in the past fortnight "
            "book a 30-minute meeting with whoever is assigned to them called 'Update on {current_customer_name}' at the first time I'm free tomorrow"
        ),
        "alternative_queries": [
            (
                "I haven't spoken to {current_customer_name} in a while. Can you check if it's been over 14 days? If so, "
                "book a 30-minute meeting with whoever is assigned to them called 'Update on {current_customer_name}' at the first time I'm free tomorrow"
            ),
            (
                "If we haven't spoken to {current_customer_name} in the past 2 weeks, book a half hour meeting with whoever"
                "is assigned to them called 'Update on {current_customer_name}' at the first time I'm free tomorrow"
            ),
        ],
        "logic": book_meeting_if_no_customer_contact_logic,
        "domains": ["crm", "calendar"],
    },
    # CRM + project management
    {
        "query": (
            " Add {new_customer_name} as a new lead in the crm and assign them to the person "
            "with the fewest overdue tasks"
        ),
        "alternative_queries": [
            (
                "I need to add {new_customer_name} as a new lead in the crm. Can you assign them to the person with the fewest overdue tasks?"
            ),
            (
                "Can you find the person with the fewest overdue tasks and assign {new_customer_name} to them as a new lead in the crm?"
            ),
        ],
        "logic": add_new_customer_fewest_overdue_tasks_logic,
        "domains": ["crm", "project_management"],
    },
    # Email + calendar
    {
        "query": """Find the email from {natural_language_email_date} about {subject} and schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} with the sender for {natural_language_event_date}.""",
        "alternative_queries": [
            "I need to schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} for {natural_language_event_date}. It's with the sender of the email from {natural_language_email_date} about '{subject}'. Can you do that?",
            "Can you find the email from {natural_language_email_date} about '{subject}' and schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} with the sender for {natural_language_event_date}?",
        ],
        "logic": find_email_schedule_event_sender_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """Send an email to attendees of the first event on {natural_language_event_date}. Title it with the event name and tell them 'Remember to attend this event.'""",
        "alternative_queries": [
            "Can you send an email to attendees of the first event on {natural_language_event_date}? Title it with the event name and tell them 'Remember to attend this event.'",
            "I need to make sure everyone remembers to attend the first event on {natural_language_event_date}. Can you send an email to the attendees with the event name as the title and 'Remember to attend this event.' in the email?",
        ],
        "logic": find_event_send_email_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If {sender_name} hasn't sent me any emails in the past {days} days, schedule a 30 minute meeting with them for {day_of_week} at {natural_language_time} called 'Catch up with {sender_name}'""",
        "alternative_queries": [
            "I can't remember the last time I heard from {sender_name}. Can you check if they've sent me any emails in the past {days} days? If not, schedule a 30 minute meeting with them for {day_of_week} at {natural_language_time} called 'Catch up with {sender_name}'",
            "if {sender_name} hasn't sent me any emails in the past {days} days, schedule a half hour meeting with them for {day_of_week} at {natural_language_time} and call it 'Catch up with {sender_name}'",
        ],
        "logic": schedule_event_if_no_emails_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If I haven't met with {name} in the past {days} days, send them an email titled 'Catch up soon?' saying 'We haven't caught up in a while - can you send some availability over next week?'""",
        "alternative_queries": [
            "can't remember the last time I met with {name}. Can you check if it's been over {days} days? If so, send them an email titled 'Catch up soon?' saying 'We haven't caught up in a while - can you send some availability over next week?'",
            "I haven't met with {name} in a while. if it's been longer than {days} days can you send them an email titled 'Catch up soon?' saying 'We haven't caught up in a while - can you send some availability over next week?'",
        ],
        "logic": send_email_if_no_past_meetings_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If I don't have any meetings scheduled with {name} in the next {days} days, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'""",
        "alternative_queries": [
            "Did I already schedule a meeting with {name} in the next {days} days? If not, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'",
            "I need to check if I have any meetings scheduled with {name} in the next {days} days. If not, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'",
        ],
        "logic": send_email_if_no_future_meetings_logic,
        "domains": ["email", "calendar"],
    },
    # Email + project management
    {
        "query": (
            "If {name} has any overdue tasks, send them an email titled 'Overdue tasks' saying 'You have a few overdue tasks - can you update me on them?'. "
            "Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
        ),
        "alternative_queries": [
            (
                "can you check if {name} has any overdue tasks? If so, send them an email titled 'Overdue tasks' saying 'You have a few overdue tasks - "
                "can you update me on them?'. Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
            ),
            (
                "I think {name} might have some overdue tasks. Can you check and if so, send them an email titled 'Overdue tasks' saying 'You have a few overdue "
                "tasks - can you update me on them?'. Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
            ),
        ],
        "logic": send_email_for_overdue_tasks_logic,
        "domains": ["email", "project_management"],
    },
    # Calendar + project management
    {
        "query": (
            "Book a half-hour meeting with {name} called 'Catch up on overdue tasks' at the earliest time I'm free tomorrow"
            "if they have any overdue tasks"
        ),
        "alternative_queries": [
            (
                "can you check if {name} has any overdue tasks? If so, book a 30 minute meeting with them called 'Catch up on overdue tasks' at the earliest time "
                "I'm free tomorrow"
            ),
            (
                "I think {name} might have some overdue tasks. Can you check and if so, book a half hour meeting with them called 'Catch up on overdue tasks' at the "
                "earliest time I'm free tomorrow"
            ),
        ],
        "logic": book_meeting_with_overdue_tasks_logic,
        "domains": ["calendar", "project_management"],
    },
    # Analytics + email
    {
        "query": (
            "If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date} "
            "send an email to {sender} titled 'Update on {natural_language_metric}' saying 'I noticed {natural_language_metric} was {more_or_less} than {threshold} - can you update me?'"
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "send an email to {sender} titled 'Update on {natural_language_metric}' saying 'I noticed {natural_language_metric} was {more_or_less} than {threshold} - can you update me?'"
            ),
            (
                "I think {natural_language_metric} might have been {more_or_less} than {threshold}. If it has been at any time since {natural_language_date}, can you"
                "send an email to {sender} titled 'Update on {natural_language_metric}' saying 'I noticed {natural_language_metric} was {more_or_less} than {threshold} - can you update me?'"
            ),
        ],
        "logic": send_email_if_metric_more_or_less_than_threshold_logic,
        "domains": ["analytics", "email"],
    },
    # Analytics + calendar
    {
        "query": (
            "If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date} "
            "schedule a half-hour meeting called 'Discuss {natural_language_metric}' with {sender_name} at the earliest time I'm free tomorrow"
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "schedule a 30 minute meeting called 'Discuss {natural_language_metric}' with {sender_name} at the earliest time I'm free tomorrow"
            ),
            (
                "I think {natural_language_metric} might have been {more_or_less} than {threshold} at any time since {natural_language_date}. Can you check and if so, "
                "schedule a half-hour meeting called 'Discuss {natural_language_metric}' with {sender_name} at the earliest time I'm free tomorrow"
            ),
        ],
        "logic": schedule_event_if_metric_more_or_less_than_threshold_logic,
        "domains": ["analytics", "calendar"],
    },
    # Analytics + project management
    {
        "query": (
            "If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date} "
            "make a backlog task called 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday"
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "make a backlog task called 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday"
            ),
            (
                "Was {natural_language_metric} {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "make a backlog task called 'Improve {natural_language_metric}' on the front-end board and assign it to for {name} with next Friday as the deadline"
            ),
        ],
        "logic": make_task_if_metric_more_or_less_than_threshold_logic,
        "domains": ["analytics", "project_management"],
    },
    {
        "query": (
            "If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date} "
            "make a backlog task called 'Improve {natural_language_metric}' on the front-end board with a deadline of next Friday"
            " for the person with the most completed front end tasks"
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "make a backlog task called 'Improve {natural_language_metric}' due next Friday on the front-end board and assign it to the person with the most completed front end tasks"
            ),
            (
                "Was {natural_language_metric} {more_or_less} than {threshold} at any time since {natural_language_date}? We need to fix this by next Friday if so "
                "- make a backlog task called 'Improve {natural_language_metric}' on the front-end board and assign it to the person with the most completed front end tasks"
            ),
        ],
        "logic": make_task_person_most_completed_if_metric_vs_threshold_logic,
        "domains": ["analytics", "project_management"],
    },
    {
        "query": (
            "Check the percent growth of {natural_language_metric} since {day_of_week} and if was more than {natural_language_metric_2} "
            "make a backlog task called 'Improve {natural_language_metric_2}' for {name} on the front-end board with a deadline of next Friday"
        ),
        "alternative_queries": [
            (
                "can you check the percent growth of {natural_language_metric} since {day_of_week}? If it grew by more than {natural_language_metric_2} "
                "make a task called 'Improve {natural_language_metric_2}' on the front-end backlog for {name} that's due next Friday"
            ),
            (
                "I need to check the percent growth of {natural_language_metric} since {day_of_week}. If it grew by more than {natural_language_metric_2} "
                "make a backlog task called 'Improve {natural_language_metric_2}' for {name} on the front-end board with a deadline of next Friday"
            ),
        ],
        "logic": make_task_if_relative_growth_logic,
        "domains": ["analytics", "project_management"],
    },
    # Analytics + CRM
    {
        "query": (
            "If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date} "
            "delete all {assigned_to_first_name}'s leads in the CRM"
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "delete all the leads assigned to {assigned_to_first_name} in the CRM"
            ),
            (
                "I think {natural_language_metric} might have been {more_or_less} than {threshold} at any time since {natural_language_date}. Can you check and if so, "
                "delete all {assigned_to_first_name}'s leads in the CRM"
            ),
        ],
        "logic": delete_all_customers_if_metric_more_than_threshold_logic,
        "domains": ["analytics", "crm"],
    },
    # Email + calendar + project management
    {
        "query": (
            "If {name} has any overdue tasks, book a half hour meeting with them called 'Catch up on overdue tasks' at the earliest time I'm free tomorrow and "
            "send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - let's catch up tomorrow.' "
            "Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
        ),
        "alternative_queries": [
            (
                "can you check if {name} has any overdue tasks? If so, book a 30 minute meeting with them called 'Catch up on overdue tasks' at the earliest time "
                "I'm free tomorrow and send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - let's catch up tomorrow.' "
                "Otherwise send them an email saying 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
            ),
            (
                "I think {name} might have some overdue tasks. Can you check and if so, book a half hour meeting with them called 'Catch up on overdue tasks' at the "
                "earliest time I'm free tomorrow and send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - let's catch up "
                "tomorrow.' Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
            ),
        ],
        "logic": book_event_send_email_if_overdue_tasks_logic,
        "domains": ["email", "calendar", "project_management"],
    },
    # Analytics + email + project management
    {
        "query": (
            "If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date} "
            "make a backlog task 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday "
            "otherwise send them an email titled 'Recent {natural_language_metric}' saying 'I noticed {natural_language_metric} has been stable, nice work!' "
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "make a task 'Improve {natural_language_metric}' for {name} on the front-end backlog with a deadline of next Friday "
                "otherwise send them an email titled 'Recent {natural_language_metric}' saying 'I noticed {natural_language_metric} has been stable, nice work!'"
            ),
            (
                "Was {natural_language_metric} {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "make a backlog task called 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday "
                "otherwise send them an email titled 'Recent {natural_language_metric}' saying 'I noticed {natural_language_metric} has been stable, nice work!'"
            ),
        ],
        "logic": make_task_or_send_email_if_metric_more_or_less_than_threshold_logic,
        "domains": ["analytics", "email", "project_management"],
    },
    # Analytics + calendar + project management
    {
        "query": (
            "Check the percent growth of {natural_language_metric} since {day_of_week} and if was more than {natural_language_metric_2} "
            "make a backlog task called 'Improve {natural_language_metric_2}' for {name} on the front-end board with a deadline of next Friday. "
            "Also schedule a half-hour meeting called 'Discuss {natural_language_metric}' with them at the first time I can do tomorrow"
        ),
        "alternative_queries": [
            (
                "can you check the percent growth of {natural_language_metric} since {day_of_week}? If it grew by more than {natural_language_metric_2} "
                "make a backlog task called 'Improve {natural_language_metric_2}' for {name} on the front-end board with a deadline of next Friday "
                "and schedule a half-hour meeting called 'Discuss {natural_language_metric}' for us at the first time I can do tomorrow"
            ),
            (
                "please check the percent growth of {natural_language_metric} since {day_of_week}. If it grew by more than {natural_language_metric_2} "
                "make a front-end backlog task called 'Improve {natural_language_metric_2}' for {name} that's due next Friday "
                "and schedule a 30 minute meeting called 'Discuss {natural_language_metric}' for us at the earliest slot i'm free tomorrow"
            ),
        ],
        "logic": make_task_and_book_meeting_if_relative_growth_logic,
        "domains": ["analytics", "calendar", "project_management"],
    },
    # Analytics + crm + email
    {
        "query": (
            "If {natural_language_metric} was more than {threshold} at any time since {natural_language_date} "
            "delete {assigned_to_first_name}'s new leads in the CRM and send them an email titled 'Reprioritising'"
            "saying '{natural_language_metric} looks good, so we no longer need you finding new leads'."
            "If not say in the email 'We need you to improve {natural_language_metric} - TBD.'"
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was more than {threshold} at any time since {natural_language_date}? If so, "
                "delete all the leads assigned to {assigned_to_first_name}'s in the CRM and send them an email titled 'Reprioritising' saying '{natural_language_metric} looks good, "
                "so we no longer need you finding new leads'. If not say 'We need you to improve {natural_language_metric} - TBD.'"
            ),
            (
                "Was {natural_language_metric} more than {threshold} at any time since {natural_language_date}? If so, "
                "delete all {assigned_to_first_name}'s leads in the CRM and then send them an email titled 'Reprioritising' saying '{natural_language_metric} looks good, "
                "so we no longer need you finding new leads'. If not say in the email 'We need you to improve {natural_language_metric} - TBD.'"
            ),
        ],
        "logic": delete_all_customers_send_email_if_metric_more_than_threshold_logic,
        "domains": ["analytics", "crm", "email"],
    },
    # Analytics + calendar + email + project management
    {
        "query": (
            "If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date} "
            "make a backlog task 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday "
            "and schedule a half-hour meeting called 'Discuss {natural_language_metric}' for us at the first time I can do tomorrow "
            "otherwise send them an email titled '{natural_language_metric}' saying 'I noticed {natural_language_metric} has been stable, nice work!''"
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "make a task 'Improve {natural_language_metric}' for {name} on the front-end backlog that's due next Friday "
                "and schedule a half-hour meeting called 'Discuss {natural_language_metric}' for us at the first time I can do tomorrow "
                "otherwise send them an email titled '{natural_language_metric}' saying 'I noticed {natural_language_metric} has been stable, nice work!''"
            ),
            (
                "Was {natural_language_metric} {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "add a task to the backlog called 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday "
                "and schedule a half hour meeting called 'Discuss {natural_language_metric}' for us at the earliest time I'm free tomorrow "
                "otherwise send them an email titled '{natural_language_metric}' saying 'I noticed {natural_language_metric} has been stable, nice work!''"
            ),
        ],
        "logic": make_task_book_meeting_or_send_email_if_metric_more_or_less_than_threshold_logic,
        "domains": ["analytics", "calendar", "email", "project_management"],
    },
    # Analytics + calendar + email + project management + crm
    {
        "query": (
            "If {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date} "
            "make a backlog task called 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday "
            "and book a half-hour meeting for us called 'Discuss {natural_language_metric}' at the earliest time I'm free tomorrow. "
            "otherwise send them an email titled 'New leads for you' saying '{natural_language_metric} looks good, so there are new leads for you' "
            "and then give them all {assigned_to_first_name}'s leads in the CRM"
        ),
        "alternative_queries": [
            (
                "can you check if {natural_language_metric} was {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "make a task for {name} on the backlog called 'Improve {natural_language_metric}' on the front-end board that's due next Friday "
                "and book a half-hour meeting for us called 'Discuss {natural_language_metric}' at the earliest time I can do tomorrow. "
                "otherwise send them an email titled 'New leads for you' saying '{natural_language_metric} looks good, so there are new leads for you' "
                "and then give them all {assigned_to_first_name}'s leads in the CRM"
            ),
            (
                "Was {natural_language_metric} {more_or_less} than {threshold} at any time since {natural_language_date}? If so, "
                "make a backlog task called 'Improve {natural_language_metric}' for {name} on the front-end board with a deadline of next Friday "
                "and book a 30 minute meeting for us called 'Discuss {natural_language_metric}' at the earliest time I'm free tomorrow. "
                "otherwise send them an email and title it 'New leads for you' saying '{natural_language_metric} looks good, so there are new leads for you' "
                "and then give them all {assigned_to_first_name}'s leads in the CRM"
            ),
        ],
        "logic": make_task_book_meeting_or_send_email_new_leads_if_metric_more_or_less_than_threshold_logic,
        "domains": ["analytics", "calendar", "email", "project_management", "crm"],
    },
]


def generate_query_and_answer():
    np.random.seed(42)
    random.seed(42)
    max_queries_per_template = 10
    generated_queries_and_answers = generate_all_queries_and_answers(MULTI_DOMAIN_TEMPLATES, max_queries_per_template)
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/multi_domain_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )


if __name__ == "__main__":
    generate_query_and_answer()
