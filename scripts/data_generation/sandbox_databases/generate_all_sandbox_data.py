import scripts.data_generation.sandbox_databases.generate_analytics_data as analytics
import scripts.data_generation.sandbox_databases.generate_calendar_data as calendar
import scripts.data_generation.sandbox_databases.generate_customer_relationship_manager_data as crm
import scripts.data_generation.sandbox_databases.generate_email_data as email
import scripts.data_generation.sandbox_databases.generate_project_management_data as project_management

domains = {
    "calendar": calendar,
    "analytics": analytics,
    "crm": crm,
    "email": email,
    "project_management": project_management,
}
for name, module in domains.items():
    print(f"Generating {name} sandbox data...")
    module.generate_data()
