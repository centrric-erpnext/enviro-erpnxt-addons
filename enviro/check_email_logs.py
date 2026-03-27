import frappe

def execute():
    print("--- CHECKING NOTIFICATION LOGS ---")
    
    # Check the Notification record
    if frappe.db.exists("Notification", "Request Client Quotation Approval"):
        doc = frappe.get_doc("Notification", "Request Client Quotation Approval")
        print(f"Notification Configuration:")
        print(f"- Event: {doc.event}")
        print(f"- Condition: {doc.condition}")
        print(f"- Target Field: {doc.value_changed if doc.event == 'Value Change' else 'N/A'}")
    else:
        print("Notification not found!")
    
    # Check Email Queue specifically for Quotations recently
    print("\n--- CHECKING EMAIL QUEUE ---")
    emails = frappe.get_all("Email Queue", 
        filters={"reference_doctype": "Quotation"}, 
        fields=["name", "status", "error", "message_id", "creation"],
        order_by="creation desc",
        limit=5
    )
    
    if emails:
        print(f"Found {len(emails)} recent emails linked to Quotations:")
        for e in emails:
            print(f"- Queue ID: {e.name} | Status: {e.status} | Created: {e.creation} | Error: {e.error}")
    else:
        print("0 emails in the Email Queue linked to a Quotation.")
        
    print("\n--- SYSTEM INFO ---")
    # Check if a contact_email existed on the most recent Quotation which had client_approval=Pending
    quotes = frappe.get_all("Quotation", 
        filters={"custom_requires_client_approval": 1, "custom_client_approval_status": "Pending"}, 
        fields=["name", "contact_email", "customer_name"],
        order_by="creation desc",
        limit=2
    )
    for q in quotes:
        print(f"Quotation {q.name}: Contact Email = '{q.contact_email}'")

