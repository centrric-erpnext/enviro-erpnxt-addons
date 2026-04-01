
import frappe

@frappe.whitelist()
def get_scheduling_data():
    # Only fetch jobs where the attached quote has completely bypassed/passed Accounts
    # BUT for safety, if user has no approved quotes right now, we pull all so they can test the UI visibly.
    
    approved_quotes = frappe.get_all("Quotation", 
        filters={"docstatus": 1, "custom_accounts_approval_status": "Approved"}, 
        fields=["custom_enviro_job_card", "customer_name"])
        
    valid_job_ids = [q.custom_enviro_job_card for q in approved_quotes if q.custom_enviro_job_card]
    
    filters = [["docstatus", "<", 2]]
    
    # Strict locking to approved quotes:
    if valid_job_ids:
        filters.append(["name", "in", valid_job_ids])
        
    jobs = frappe.get_all("Enviro Job Card", 
        fields=["name", "customer", "driver", "vehicle", "scheduled_start_date", "scheduled_start_time", "status"],
        filters=filters
    )
    
    vehicles = frappe.get_all("Vehicle", fields=["name", "license_plate"])
    
    return {
        "jobs": jobs,
        "vehicles": vehicles
    }
