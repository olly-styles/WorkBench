import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)
import warnings

warnings.filterwarnings("ignore")  # supress pandas warning

import scripts.data_generation.query_answer_generation.generate_analytics_query_and_answer as analytics
import scripts.data_generation.query_answer_generation.generate_calendar_query_and_answer as calendar
import scripts.data_generation.query_answer_generation.generate_customer_relationship_manager_query_and_answer as crm
import scripts.data_generation.query_answer_generation.generate_email_query_and_answer as email
import scripts.data_generation.query_answer_generation.generate_project_management_query_and_answer as project_management
import scripts.data_generation.query_answer_generation.generate_multi_domain_query_and_answer as multi_domain

domains = {
    "analytics": analytics,
    "calendar": calendar,
    "crm": crm,
    "email": email,
    "project_management": project_management,
    "multi_domain": multi_domain,
}
for domain in domains:
    print(f"Generating {domain} query and answer data...")
    domains[domain].generate_query_and_answer()
