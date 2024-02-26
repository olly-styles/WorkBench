import pandas as pd
from langchain.tools import tool

CRM_DATA = pd.read_csv("data/processed/customer_relationship_manager_data.csv", dtype=str)


def reset_state():
    """
    Resets the CRM data to the original state.
    """
    global CRM_DATA
    CRM_DATA = pd.read_csv("data/processed/customer_relationship_manager_data.csv", dtype=str)


@tool("customer_relationship_manager.search_customers", return_direct=False)
def search_customers(
    customer_name=None,
    customer_email=None,
    product_interest=None,
    status=None,
    assigned_to=None,
    last_contact_date_min=None,
    last_contact_date_max=None,
    follow_up_by_min=None,
    follow_up_by_max=None,
):
    """
    Searches for customers based on the given parameters.

    Parameters
    ----------
    customer_name : str, optional
        Name of the customer.
    customer_email : str, optional
        Email address of the customer.
    product_interest : str, optional
        Product interest of the customer.
    status : str, optional
        Current status of the customer.
    assigned_to : str, optional
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
    customers : dict
        Customer information for the given parameters. Returns at most 5 records.

    Examples
    --------
    >>> crm.search_customers(customer_name="John")
    {{"customer_id": "00000001", "assigned_to": "sam@example.com", "customer_name": "John Smith",
    "customer_email": "john.smith@example.com", "customer_phone": "123-456-7890", "last_contact_date": "2023-01-01",
    "product_interest": "Software", "status": "Qualified", "follow_up_by": "2023-01-15", "notes": "Had a call on 2023-01-01. "}}
    """
    customers = CRM_DATA.copy()
    if not any(
        [
            customer_name,
            customer_email,
            product_interest,
            status,
            assigned_to,
            last_contact_date_min,
            last_contact_date_max,
            follow_up_by_min,
            follow_up_by_max,
        ]
    ):
        return "No search parameters provided. Please provide at least one parameter."

    if customer_name:
        customers = customers[customers["customer_name"].str.contains(customer_name, case=False)]
    if customer_email:
        customers = customers[customers["customer_email"].str.contains(customer_email, case=False)]
    if product_interest:
        customers = customers[customers["product_interest"].str.contains(product_interest, case=False)]
    if status:
        customers = customers[customers["status"].str.contains(status, case=False)]
    if assigned_to:
        customers = customers[customers["assigned_to"].str.contains(assigned_to, case=False)]
    if last_contact_date_min:
        customers = customers[customers["last_contact_date"] >= last_contact_date_min]
    if last_contact_date_max:
        customers = customers[customers["last_contact_date"] <= last_contact_date_max]
    if follow_up_by_min:
        customers = customers[customers["follow_up_by"] >= follow_up_by_min]
    if follow_up_by_max:
        customers = customers[customers["follow_up_by"] <= follow_up_by_max]
    return customers.to_dict(orient="records")[:5]


@tool("customer_relationship_manager.update_customer", return_direct=False)
def update_customer(customer_id=None, field=None, new_value=None):
    """
    Updates a customer record by ID.

    Parameters
    ----------
    customer_id : str
        ID of the customer.
    field : str
        Field to update. Available fields are: "customer_name", "assigned_to", "customer_email", "customer_phone", "last_contact_date", "product_interest", "status", "notes", "follow_up_by"
    new_value : str
        New value for the field.

    Returns
    -------
    message : str
        Message indicating the status of the update.

    Examples
    --------
    >>> crm.update_customer("00000001", "status", "Won")
    "Customer updated successfully."
    """
    global CRM_DATA

    if not customer_id or not field or not new_value:
        return "Customer ID, field, or new value not provided."
    
    if field == "status" and new_value not in ["Qualified", "Won", "Lost", "Lead", "Proposal"]:
        return "Status not valid. Please choose from: 'Qualified', 'Won', 'Lost', 'Lead', 'Proposal'"

    if field == "product_interest" and new_value not in ["Software", "Hardware", "Services", "Consulting", "Training"]:
        return "Product interest not valid. Please choose from: 'Software', 'Hardware', 'Services', 'Consulting', 'Training'"            

    if customer_id in CRM_DATA["customer_id"].values:
        if field in CRM_DATA.columns:
            CRM_DATA.loc[CRM_DATA["customer_id"] == customer_id, field] = new_value
            return "Customer updated successfully."
        else:
            return "Field not valid. Please choose from: 'customer_name', 'assigned_to', 'customer_email', 'customer_phone', 'last_contact_date', 'product_interest', 'status', 'notes', 'follow_up_by'"
    else:
        return "Customer not found."


@tool("customer_relationship_manager.add_customer", return_direct=False)
def add_customer(
    customer_name=None,
    assigned_to=None,
    status=None,
    customer_email=None,
    customer_phone=None,
    last_contact_date=None,
    product_interest=None,
    notes="",
    follow_up_by=None,
):
    """
    Adds a new customer record.

    Parameters
    ----------
    customer_name : str
        Name of the customer.
    assigned_to : str
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
    global CRM_DATA
    if not all([customer_name, assigned_to, status]):
        return "Please provide all required fields: customer_name, assigned_to, status."

    new_id = str(int(CRM_DATA["customer_id"].max()) + 1).zfill(8)
    new_customer = pd.DataFrame(
        {
            "customer_id": [new_id],
            "customer_name": [customer_name],
            "customer_email": [customer_email],
            "customer_phone": [customer_phone],
            "last_contact_date": [last_contact_date],
            "product_interest": [product_interest],
            "status": [status],
            "assigned_to": [assigned_to],
            "notes": [notes],
            "follow_up_by": [follow_up_by],
        }
    )
    CRM_DATA = pd.concat([CRM_DATA, new_customer], ignore_index=True)
    return new_id


@tool("customer_relationship_manager.delete_customer", return_direct=False)
def delete_customer(customer_id=None):
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
    global CRM_DATA
    if not customer_id:
        return "Customer ID not provided."
    if customer_id not in CRM_DATA["customer_id"].values:
        return "Customer not found."
    CRM_DATA = CRM_DATA[CRM_DATA["customer_id"] != customer_id]
    return "Customer deleted successfully."
