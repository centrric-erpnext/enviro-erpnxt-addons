
import frappe

@frappe.whitelist()
def get_scheduling_data():
    # Only fetch jobs where the attached quote has completely bypassed/passed Accounts
    
    approved_quotes = frappe.get_all("Quotation", 
        filters={"docstatus": 1, "custom_accounts_approval_status": "Approved"}, 
        fields=["custom_enviro_job_card", "customer_name"])
        
    valid_job_ids = [q.custom_enviro_job_card for q in approved_quotes if q.custom_enviro_job_card]
    
    filters = [["docstatus", "<", 2]]
    
    # Strict locking to approved quotes ONLY:
    if valid_job_ids:
        filters.append(["name", "in", valid_job_ids])
    else:
        # If no approved quotes exist, return an empty tracking list for extreme security
        filters.append(["name", "=", "NONE_AUTHORIZED"])
        
    jobs = frappe.get_all("Enviro Job Card", 
        fields=["name", "customer", "driver", "vehicle", "scheduled_start_date", "scheduled_start_time", 
                "status", "is_reoccurring_quote", "is_outsourced_job", "frequency_in_weeks", "job_card_type"],
        filters=[["name", "in", valid_job_ids]]
    )
    
    vehicles = frappe.get_all("Vehicle", fields=["name", "license_plate"])
    
    return {
        "jobs": jobs,
        "vehicles": vehicles
    }

@frappe.whitelist()
def api_schedule_job(job_id, payload):
    import json
    data = json.loads(payload)
    
    doc = frappe.get_doc("Enviro Job Card", job_id)
    doc.scheduled_start_date = data.get("scheduled_start_date")
    doc.scheduled_start_time = data.get("scheduled_start_time")
    doc.scheduled_end_date = data.get("scheduled_end_date")
    doc.scheduled_end_time = data.get("scheduled_end_time")
    doc.vehicle = data.get("vehicle")
    doc.driver = data.get("driver")
    doc.status = "Assigned"
    
    doc.set("team_members", [])
    team = data.get("team_members")
    if team:
        for member in team:
            doc.append("team_members", {"employee": member})
            
    doc.save(ignore_permissions=True)
    return "OK"

@frappe.whitelist()
def cancel_job_card(job_id):
    frappe.db.set_value("Enviro Job Card", job_id, "status", "Cancelled")
    return "OK"
