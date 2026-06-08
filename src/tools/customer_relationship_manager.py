import json

import pandas as pd

from src.tools._utils import DEFAULT_SEARCH_RESULT_LIMIT, delete_record, generate_next_id, normalize_email
from src.tools.state import get_state
from src.tools.tool import tool

VALID_STATUSES = ["Qualified", "Won", "Lost", "Lead", "Proposal"]
VALID_PRODUCT_INTERESTS = ["Software", "Hardware", "Services", "Consulting", "Training"]


@tool("customer_relationship_manager.search_customers")
def search_customers(
    customer_name: str | None = None,
    customer_email: str | None = None,
    product_interest: str | None = None,
    status: str | None = None,
    assigned_to_email: str | None = None,
    last_contact_date_min: str | None = None,
    last_contact_date_max: str | None = None,
    follow_up_by_min: str | None = None,
    follow_up_by_max: str | None = None,
) -> str:
    """
    Searches for customers based on the given parameters.

    Parameters
    ----------
    customer_name : str, optional
        Name of the customer.
    customer_email : str, optional
        Email address of the customer.
    product_interest : str, optional
        Product interest of the customer. One of: "Software", "Hardware", "Services", "Consulting", "Training".
    status : str, optional
        Current status of the customer. One of: "Qualified", "Won", "Lost", "Lead", "Proposal".
    assigned_to_email : str, optional
        Email address of the person assigned to the customer.
    last_contact_date_min : str, optional
        Minimum last contact date. Format: "YYYY-MM-DD"
    last_contact_date_max : str, optional
        Maximum last contact date. Format: "YYYY-MM-DD"
    follow_up_by_min : str, optional
        Minimum follow up date. Format: "YYYY-MM-DD"
    follow_up_by_max : str, optional
        Maximum follow up date. Format: "YYYY-MM-DD"

    Returns
    -------
    customers : list
        List of customers matching the given parameters. Returns at most 5 customers.

    Examples
    --------
    >>> crm.search_customers(customer_name="John")
    {{"customer_id": "00000001", "assigned_to_email": "sam@example.com", "customer_name": "John Smith",
    "customer_email": "john.smith@example.com", "customer_phone": "123-456-7890", "last_contact_date": "2023-01-01",
    "product_interest": "Software", "status": "Qualified", "follow_up_by": "2023-01-15", "notes": "Had a call on 2023-01-01. "}}
    """
    state = get_state()
    customers = state.crm_data.copy()
    if not any(
        (
            customer_name,
            customer_email,
            product_interest,
            status,
            assigned_to_email,
            last_contact_date_min,
            last_contact_date_max,
            follow_up_by_min,
            follow_up_by_max,
        )
    ):
        return "No search parameters provided. Please provide at least one parameter."

    if customer_name:
        customers = customers[customers["customer_name"].str.contains(customer_name, case=False, regex=False)]
    if customer_email:
        customers = customers[customers["customer_email"].str.contains(customer_email, case=False, regex=False)]
    if product_interest:
        customers = customers[customers["product_interest"].str.contains(product_interest, case=False, regex=False)]
    if status:
        customers = customers[customers["status"].str.contains(status, case=False, regex=False)]
    if assigned_to_email:
        customers = customers[customers["assigned_to_email"].str.contains(assigned_to_email, case=False, regex=False)]
    if last_contact_date_min:
        customers = customers[customers["last_contact_date"] >= last_contact_date_min]
    if last_contact_date_max:
        customers = customers[customers["last_contact_date"] <= last_contact_date_max]
    if follow_up_by_min:
        customers = customers[customers["follow_up_by"] >= follow_up_by_min]
    if follow_up_by_max:
        customers = customers[customers["follow_up_by"] <= follow_up_by_max]
    results = customers.to_dict(orient="records")
    return json.dumps(results[:DEFAULT_SEARCH_RESULT_LIMIT])


@tool("customer_relationship_manager.update_customer")
def update_customer(customer_id: str | None = None, field: str | None = None, new_value: str | None = None) -> str:
    """
    Updates a customer record by ID.

    Parameters
    ----------
    customer_id : str
        ID of the customer.
    field : str
        Field to update. Available fields are: "customer_name", "assigned_to_email", "customer_email", "customer_phone", "last_contact_date", "product_interest", "status", "notes", "follow_up_by"
    new_value : str
        New value for the field. When field is "status", one of: "Qualified", "Won", "Lost", "Lead", "Proposal". When field is "product_interest", one of: "Software", "Hardware", "Services", "Consulting", "Training".

    Returns
    -------
    message : str
        Message indicating the status of the update.

    Examples
    --------
    >>> crm.update_customer("00000001", "status", "Won")
    "Customer updated successfully."
    """
    state = get_state()

    if not customer_id or not field or not new_value:
        return "Customer ID, field, or new value not provided."

    if field == "status" and new_value not in VALID_STATUSES:
        return f"Status not valid. Please choose from: {', '.join(repr(v) for v in VALID_STATUSES)}"

    if field == "product_interest" and new_value not in VALID_PRODUCT_INTERESTS:
        return f"Product interest not valid. Please choose from: {', '.join(repr(v) for v in VALID_PRODUCT_INTERESTS)}"

    if field in ("customer_email", "assigned_to_email"):
        new_value = normalize_email(new_value)

    if customer_id not in state.crm_data["customer_id"].values:
        return "Customer not found."
    if field not in state.crm_data.columns:
        return "Field not valid. Please choose from: 'customer_name', 'assigned_to_email', 'customer_email', 'customer_phone', 'last_contact_date', 'product_interest', 'status', 'notes', 'follow_up_by'"
    state.crm_data.loc[state.crm_data["customer_id"] == customer_id, field] = new_value
    return "Customer updated successfully."


@tool("customer_relationship_manager.add_customer")
def add_customer(
    customer_name: str | None = None,
    assigned_to_email: str | None = None,
    status: str | None = None,
    customer_email: str | None = None,
    customer_phone: str | None = None,
    last_contact_date: str | None = None,
    product_interest: str | None = None,
    notes: str = "",
    follow_up_by: str | None = None,
) -> str:
    """
    Adds a new customer record.

    Parameters
    ----------
    customer_name : str
        Name of the customer.
    assigned_to_email : str
        Email address of the person assigned to the customer.
    status : str
        Current status of the customer. One of: "Qualified", "Won", "Lost", "Lead", "Proposal"
    customer_email : str, optional
        Email address of the customer.
    customer_phone : str, optional
        Phone number of the customer.
    last_contact_date : str, optional
        The last date the customer was contacted. Format: "YYYY-MM-DD"
    product_interest : str, optional
        Product interest of the customer. One of: "Software", "Hardware", "Services", "Consulting", "Training"
    notes : str, optional, optional
        Notes about the customer.
    follow_up_by : str, optional
        Date for the next follow up. Format: "YYYY-MM-DD"

    Returns
    -------
    customer_id : str
        ID of the new customer.

    Examples
    --------
    >>> crm.add_customer("Sam Smith", "sam@example.com", "Lead", "sam.smith@example.com", "123-456-7890", "2023-01-01", "Software")
    "00000201"
    """
    state = get_state()
    if not all((customer_name, assigned_to_email, status)):
        return "Please provide all required fields: customer_name, assigned_to_email, status."

    assert assigned_to_email is not None
    assigned_to_email = normalize_email(assigned_to_email)
    if customer_email:
        customer_email = normalize_email(customer_email)

    new_id = generate_next_id(state.crm_data, "customer_id")
    new_customer = pd.DataFrame(
        {
            "customer_id": [new_id],
            "customer_name": [customer_name],
            "customer_email": [customer_email],
            "customer_phone": [customer_phone],
            "last_contact_date": [last_contact_date],
            "product_interest": [product_interest],
            "status": [status],
            "assigned_to_email": [assigned_to_email],
            "notes": [notes],
            "follow_up_by": [follow_up_by],
        }
    )
    state.crm_data = pd.concat([state.crm_data, new_customer], ignore_index=True)
    return new_id


@tool("customer_relationship_manager.delete_customer")
def delete_customer(customer_id: str | None = None) -> str:
    """
    Deletes a customer record by ID.

    Parameters
    ----------
    customer_id : str
        ID of the customer.

    Returns
    -------
    message : str
        Message indicating the status of the deletion.

    Examples
    --------
    >>> crm.delete_customer("00000001")
    "Customer deleted successfully."
    """
    state = get_state()
    state.crm_data, message = delete_record(state.crm_data, "customer_id", customer_id, "Customer")
    return message
