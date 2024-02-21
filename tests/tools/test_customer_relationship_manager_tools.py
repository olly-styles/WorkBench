import pandas as pd
import pytest
from src.tools import customer_relationship_manager as crm

test_customers = [
    {
        "customer_id": "00000001",
        "customer_name": "John Smith",
        "assigned_to": "email1@test.com",
        "customer_email": "customeremail1@test.com",
        "customer_phone": "123-456-7890",
        "last_contact_date": "2023-01-01",
        "product_interest": "Software",
        "status": "Qualified",
        "notes": "Had a call on 2023-01-01.",
        "follow_up_by": "2023-01-15",
    },
    {
        "customer_id": "00000002",
        "customer_name": "Jane Doe",
        "assigned_to": "email2@test.com",
        "customer_email": "customeremail2@test.com",
        "customer_phone": "123-456-7890",
        "last_contact_date": "2023-01-01",
        "product_interest": "Hardware",
        "status": "Lead",
        "notes": "Had a call on 2023-01-01.",
        "follow_up_by": "2023-01-15",
    },
]

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Load test data
    crm.CRM_DATA = pd.DataFrame(test_customers)
    # This will run before each test
    yield
    # Teardown: Reset state after each test
    crm.reset_state()


def test_search_customers():
    """
    Tests search_customers.
    """
    assert crm.search_customers.func("John")[0] == {
        "customer_id": "00000001",
        "customer_name": "John Smith",
        "assigned_to": "email1@test.com",
        "customer_email": "customeremail1@test.com",
        "customer_phone": "123-456-7890",
        "last_contact_date": "2023-01-01",
        "product_interest": "Software",
        "status": "Qualified",
        "notes": "Had a call on 2023-01-01.",
        "follow_up_by": "2023-01-15",
    }
    
def test_search_customers_no_parameters():
    """
    Tests search_customers with no parameters.
    """
    assert crm.search_customers.func() == "No search parameters provided. Please provide at least one parameter."

def test_update_customer():
    """
    Tests update_customer.
    """
    assert crm.update_customer.func("00000001", "status", "Won") == "Customer updated successfully."
    assert crm.CRM_DATA.loc[crm.CRM_DATA["customer_id"] == "00000001", "status"].values[0] == "Won"

def test_update_customer_missing_args():
    """
    Tests update_customer with missing arguments.
    """
    assert crm.update_customer.func() == "Customer ID, field, or new value not provided."
    assert crm.update_customer.func("00000001") == "Customer ID, field, or new value not provided."
    assert crm.update_customer.func("00000001", "status") == "Customer ID, field, or new value not provided."

def test_update_customer_invalid_field():
    """
    Tests update_customer with an invalid field.
    """
    assert crm.update_customer.func("00000001", "non_existent_field", "Won") == "Field not valid. Please choose from: 'customer_name', 'assigned_to', 'customer_email', 'customer_phone', 'last_contact_date', 'product_interest', 'status', 'notes', 'follow_up_by'"

def test_update_customer_customer_not_found():
    """
    Tests update_customer with a non-existent customer.
    """
    assert crm.update_customer.func("00000003", "status", "Won") == "Customer not found."

def test_add_customer():
    """
    Tests add_customer.
    """
    new_id = crm.add_customer.func("John Smith", "email@example.com", "email@example.com", "123-456-7890", "2023-01-01", "Software", "Qualified")
    assert new_id == "00000003"
    
    new_customer = crm.CRM_DATA.loc[crm.CRM_DATA["customer_id"] == "00000003"]
    assert new_customer["customer_name"].values[0] == "John Smith"
    
def test_add_customer_missing_args():
    """
    Tests add_customer with missing arguments.
    """
    assert crm.add_customer.func() == "Please provide all required fields: customer_name, assigned_to, customer_email, last_contact_date, product_interest, status."
    assert crm.add_customer.func("John Smith") == "Please provide all required fields: customer_name, assigned_to, customer_email, last_contact_date, product_interest, status."                                    
    
def test_delete_customer():
    """
    Tests delete_customer.
    """
    message = crm.delete_customer.func("00000001")
    assert message == "Customer deleted successfully."
    assert "00000001" not in crm.CRM_DATA["customer_id"].values

def test_delete_customer_no_id_provided():
    """
    Tests delete_customer with no customer_id provided.
    """
    message = crm.delete_customer.func()
    assert message == "Customer ID not provided."

def test_delete_customer_not_found():
    """
    Tests delete_customer with a non-existent customer.
    """
    message = crm.delete_customer.func("00000003")
    assert message == "Customer not found."