import pandas as pd
from scripts.data_generation.mocked_data.generate_customer_relationship_manager_data import sales_team_emails
from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME

crm_data = pd.read_csv("data/processed/customer_relationship_manager_data.csv")


def test_no_two_customers_same_name():
    """
    Tests that no two customers have the same name.
    """
    grouped = crm_data.groupby("customer_name").size()
    assert len(grouped[grouped > 1]) == 0


def test_sales_team_assigned_to_email_customers():
    """
    Tests that only sales team members are assigned to customers.
    """
    assert crm_data["assigned_to_email"].isin(sales_team_emails).all()


def test_project_management_team_not_assigned_to_email_customers():
    """
    Tests that no project management team members are assigned to customers.
    """
    from scripts.data_generation.mocked_data.generate_project_management_data import project_management_team_emails

    assert not crm_data["assigned_to_email"].isin(project_management_team_emails).any()


def test_no_two_customers_same_email():
    """
    Tests that no two customers have the same email.
    """
    grouped = crm_data.groupby("customer_email").size()
    assert len(grouped[grouped > 1]) == 0


def test_no_last_contact_date_in_future():
    """
    Tests that no customer has a last contact date in the future.
    """
    assert (crm_data["last_contact_date"] <= str(HARDCODED_CURRENT_TIME.date())).all()


def test_follow_up_dates_after_last_contact_dates():
    """
    Tests that all follow-up dates are after the last contact dates.
    """
    assert (crm_data["follow_up_by"] >= crm_data["last_contact_date"]).all()
