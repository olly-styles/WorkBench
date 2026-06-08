import warnings

import scripts.data_generation.task_outcome_generation.generate_analytics_task_and_outcome as analytics
import scripts.data_generation.task_outcome_generation.generate_calendar_task_and_outcome as calendar
import scripts.data_generation.task_outcome_generation.generate_customer_relationship_manager_task_and_outcome as crm
import scripts.data_generation.task_outcome_generation.generate_email_task_and_outcome as email
import scripts.data_generation.task_outcome_generation.generate_multi_domain_task_and_outcome as multi_domain
import scripts.data_generation.task_outcome_generation.generate_project_management_task_and_outcome as project_management

warnings.filterwarnings("ignore")  # supress pandas warning

domains = {
    "analytics": analytics,
    "calendar": calendar,
    "crm": crm,
    "email": email,
    "project_management": project_management,
    "multi_domain": multi_domain,
}
for name, module in domains.items():
    print(f"Generating {name} task and outcome data...")
    module.generate_task_and_outcome()
