from src.tools import calendar, email, analytics, project_management

all_tools = [
    calendar.get_event_information_by_id,
    calendar.search_events,
    calendar.create_event,
    calendar.delete_event,
    calendar.update_event,
    email.get_email_information_by_id,
    email.search_emails,
    email.send_email,
    email.delete_email,
    email.forward_email,
    email.reply_email,
    analytics.engaged_users_count,
    analytics.get_visitor_information_by_id,
    analytics.traffic_source_count,
    analytics.total_visits_count,
    analytics.create_plot,
    project_management.get_task_information_by_id,
    project_management.search_tasks,
    project_management.create_task,
    project_management.delete_task,
    project_management.update_task,
]

tool_information = [
    {
        "toolkit": tool.__module__,
        "tool": tool,
        "name": tool.name,
    }
    for tool in all_tools
]

calendar_toolkit = [t["tool"] for t in tool_information if t["name"].split(".")[0] == "calendar"]
email_toolkit = [t["tool"] for t in tool_information if t["name"].split(".")[0] == "email"]
analytics_toolkit = [t["tool"] for t in tool_information if t["name"].split(".")[0] == "analytics"]
project_management_toolkit = [t["tool"] for t in tool_information if t["name"].split(".")[0] == "project_management"]