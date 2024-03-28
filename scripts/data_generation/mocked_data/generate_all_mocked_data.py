import sys
import os
project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

import scripts.data_generation.mocked_data.generate_calendar_data as calendar
import scripts.data_generation.mocked_data.generate_analytics_data as analytics
import scripts.data_generation.mocked_data.generate_customer_relationship_manager_data as crm
import scripts.data_generation.mocked_data.generate_email_data as email
import scripts.data_generation.mocked_data.generate_project_management_data as project_management

domains = {
    "calendar": calendar,
    "analytics": analytics,
    "crm": crm,
    "email": email,
    "project_management": project_management,
}
for domain in domains:
    print(f"Generating {domain} sandbox data...")
    domains[domain].generate_data()
