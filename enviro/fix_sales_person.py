import frappe

def execute():
    script_name = "Generate Driver Job Cards"
    doc = frappe.get_doc("Server Script", script_name)
    
    new_script = """
# Loop through the services quoted to the customer
for item in doc.items:
    
    # Grab the Job Card Type the salesperson selected (default to Standard if left blank)
    job_type = item.get("custom_job_card_type") or "Standard"
    
    # Fetch Site details if available
    site_details = {}
    if doc.get("custom_site"):
        site_details = frappe.db.get_value("Site", doc.custom_site, 
            ["site_email_address", "industry_type", "site_address", "site_contact_person", "site_contact_mobile"], as_dict=1) or {}

    # Find a valid Sales Person (Mandatory field on Job Card)
    sales_person = doc.get("sales_person")
    if not sales_person or not frappe.db.exists("Sales Person", sales_person):
        # Fallback 1: Try to find any Sales Person linked to the owner
        sales_person = frappe.db.get_value("Sales Person", {"employee": ["in", frappe.get_all("Employee", filters={"user_id": doc.owner}, pluck="name")]}, "name")
        
        # Fallback 2: Use "Sales Team" or the first available Sales Person
        if not sales_person:
            sales_person = frappe.db.get_value("Sales Person", {"name": "Sales Team"}, "name") or frappe.db.get_value("Sales Person", {}, "name")

    # Create the new driver task
    new_job = frappe.get_doc({
        "doctype": "Enviro Job Card",
        "job_card_type": job_type,
        "source_quotation": doc.name,
        "customer": doc.get("party_name") or doc.get("customer"),
        "site": doc.get("custom_site"),
        "status": "Open",
        "job_instructions": f"Task: {item.item_name}\\nDescription: {item.description or ''}\\nQty: {item.qty}",
        
        # New Mandatory Fields (Automated from Site/Quotation)
        "site_name": doc.get("custom_site") or "Enviro Site",
        "site_contact_email": site_details.get("site_email_address") or doc.get("custom_site_email") or "",
        "industry_type": site_details.get("industry_type") or "Foods",
        "sales_person": sales_person,
        
        # Secondary Logistics Data
        "site_address": site_details.get("site_address", ""),
        "site_contact_name": site_details.get("site_contact_person", ""),
        "site_contact_mob": site_details.get("site_contact_mobile", ""),
        "job_creation_date": frappe.utils.today()
    })
    
    new_job.insert(ignore_permissions=True)
    
frappe.msgprint(f"Driver Job Cards successfully generated and sent to Dispatch.")
"""
    
    doc.script = new_script.strip()
    doc.save()
    frappe.db.commit()
    print("Successfully fixed Sales Person fallback in Server Script!")
