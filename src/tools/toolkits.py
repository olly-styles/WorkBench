from src.tools import analytics, calendar, company_directory, customer_relationship_manager, email, project_management
from src.tools.tool import Tool

tools_with_side_effects: list[Tool] = [
    calendar.create_event,
    calendar.delete_event,
    calendar.update_event,
    email.send_email,
    email.delete_email,
    email.forward_email,
    email.reply_email,
    analytics.create_plot,
    project_management.create_task,
    project_management.delete_task,
    project_management.update_task,
    customer_relationship_manager.update_customer,
    customer_relationship_manager.add_customer,
    customer_relationship_manager.delete_customer,
]

all_tools: list[Tool] = tools_with_side_effects + [
    calendar.get_event_information_by_id,
    calendar.search_events,
    email.get_email_information_by_id,
    email.search_emails,
    analytics.engaged_users_count,
    analytics.get_visitor_information_by_id,
    analytics.traffic_source_count,
    analytics.total_visits_count,
    analytics.get_average_session_duration,
    project_management.get_task_information_by_id,
    project_management.search_tasks,
    customer_relationship_manager.search_customers,
    company_directory.find_email_address,
]


def _tools_for_prefix(prefix: str) -> list[Tool]:
    return [t for t in all_tools if t.name.startswith(prefix + ".")]


calendar_toolkit: list[Tool] = _tools_for_prefix("calendar")
email_toolkit: list[Tool] = _tools_for_prefix("email")
analytics_toolkit: list[Tool] = _tools_for_prefix("analytics")
project_management_toolkit: list[Tool] = _tools_for_prefix("project_management")
customer_relationship_manager_toolkit: list[Tool] = _tools_for_prefix("customer_relationship_manager")
company_directory_toolkit: list[Tool] = _tools_for_prefix("company_directory")
