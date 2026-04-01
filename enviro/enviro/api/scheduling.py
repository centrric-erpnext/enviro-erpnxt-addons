
import frappe

@frappe.whitelist()
def get_scheduling_data():
    # 1. Block any Job Card tied to a Quotation that hasn't fully passed the Accounts Desktop.
    
    # Catch quotes that are submitted but Accounts hasn't approved
    blocked_quotes = frappe.get_all("Quotation", 
        filters=[["docstatus", "=", 1], ["custom_accounts_approval_status", "!=", "Approved"]],
        fields=["custom_enviro_job_card"]
    )
    
    # Catch any Draft quotes
    blocked_drafts = frappe.get_all("Quotation",
        filters={"docstatus": 0},
        fields=["custom_enviro_job_card"]
    )
    
    blocked_ids = [q.custom_enviro_job_card for q in blocked_quotes if q.custom_enviro_job_card]
    blocked_ids += [q.custom_enviro_job_card for q in blocked_drafts if q.custom_enviro_job_card]
    blocked_ids = list(set(blocked_ids))
    
    # Base Job query
    filters = [["docstatus", "<", 2]]
    
    # Systematically HIDE any jobs belonging to un-approved quotes
    if blocked_ids:
        filters.append(["name", "not in", blocked_ids])
        
    jobs = frappe.get_all("Enviro Job Card", 
        fields=["name", "customer", "driver", "vehicle", "scheduled_start_date", "scheduled_start_time", "status"],
        filters=filters
    )
    
    vehicles = frappe.get_all("Vehicle", fields=["name", "license_plate"])
    
    return {
        "jobs": jobs,
        "vehicles": vehicles
    }
