from src.tools import calendar, email

tool_information = [
    {
        "toolkit": "calendar",
        "tool": calendar.get_event_information_by_id,
        "name": calendar.get_event_information_by_id.name,
        "side_effects": False,
    },
    {
        "toolkit": "calendar",
        "tool": calendar.search_events,
        "name": calendar.search_events.name,
        "side_effects": False,
    },
    {
        "toolkit": "calendar",
        "tool": calendar.create_event,
        "name": calendar.create_event.name,
        "side_effects": True,
    },
    {
        "toolkit": "calendar",
        "tool": calendar.delete_event,
        "name": calendar.delete_event.name,
        "side_effects": True,
    },
    {
        "toolkit": "calendar",
        "tool": calendar.update_event,
        "name": calendar.update_event.name,
        "side_effects": True,
    },
    {
        "toolkit": "email",
        "tool": email.get_email_information_by_id,
        "name": email.get_email_information_by_id.name,
        "side_effects": False,
    },
    {
        "toolkit": "email",
        "tool": email.search_emails,
        "name": email.search_emails.name,
        "side_effects": False,
    },
    {
        "toolkit": "email",
        "tool": email.send_email,
        "name": email.send_email.name,
        "side_effects": True,
    },
    {
        "toolkit": "email",
        "tool": email.delete_email,
        "name": email.delete_email.name,
        "side_effects": True,
    },
]

calendar_toolkit = [tool for tool in tool_information if tool["toolkit"] == "calendar"]
email_toolkit = [tool for tool in tool_information if tool["toolkit"] == "email"]
