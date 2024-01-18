from src.tools import calendar, email

calendar_toolkit = [
    calendar.get_event_information_by_id,
    calendar.search_events,
    calendar.create_event,
    calendar.delete_event,
    calendar.update_event,
]

email_toolkit = [
    email.get_email_information_by_id,
    email.search_emails,
    email.send_email,
    email.delete_email,
]
