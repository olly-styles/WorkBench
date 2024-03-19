from src.tools import calendar, email, analytics, project_management, customer_relationship_manager, company_directory

tools_with_side_effects = [
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

tools_without_side_effects = [
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
    company_directory.find_email_address_by_name,
]

all_tools = tools_with_side_effects + tools_without_side_effects

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
customer_relationship_manager_toolkit = [
    t["tool"] for t in tool_information if t["name"].split(".")[0] == "customer_relationship_manager"
]
company_directory_toolkit = [t["tool"] for t in tool_information if t["name"].split(".")[0] == "company_directory"]
