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
        
    # Queue Jobs = Master Requests that aren't purely scheduled one-offs
    queue_jobs = frappe.get_all("Enviro Job Card", 
        fields=["name", "customer", "driver", "vehicle", "scheduled_start_date", "scheduled_start_time", 
                "status", "is_reoccurring_quote", "is_outsourced_job", "frequency_in_weeks", "job_card_type", "source_quotation"],
        filters=filters
    )
    
    # Calculate Waste Type for Queue Jobs
    for job in queue_jobs:
        if job.source_quotation:
            w_types = frappe.db.sql('''
                SELECT DISTINCT custom_waste_type 
                FROM `tabQuotation Item` 
                WHERE parent = %s AND custom_waste_type IS NOT NULL AND custom_waste_type != ''
            ''', job.source_quotation)
            if w_types:
                job.waste_type_label = ", ".join([w[0] for w in w_types])
            else:
                job.waste_type_label = "Standard"
        else:
            job.waste_type_label = "Manual Job"
            
    # Scheduled Jobs = Physical executions on the calendar
    scheduled_jobs = frappe.get_all("Enviro Job", 
        fields=["name", "customer", "driver", "vehicle", "scheduled_start_date", "scheduled_start_time", "status"]
    )
    
    vehicles = frappe.get_all("Vehicle", fields=["name", "license_plate", "custom_vehicle_category"])
    
    return {
        "queue_jobs": queue_jobs,
        "scheduled_jobs": scheduled_jobs,
        "vehicles": vehicles
    }

@frappe.whitelist()
def api_schedule_job(job_id, payload):
    import json
    data = json.loads(payload)
    
    # 1. Spawn a new Enviro Job directly mapping the source card
    job_card = frappe.get_doc("Enviro Job Card", job_id)
    
    new_job = frappe.new_doc("Enviro Job")
    new_job.source_job_card = job_card.name
    new_job.quotation = job_card.source_quotation
    new_job.customer = job_card.customer
    new_job.site = job_card.site
    
    new_job.scheduled_start_date = data.get("scheduled_start_date")
    new_job.scheduled_start_time = data.get("scheduled_start_time")
    new_job.scheduled_end_date = data.get("scheduled_end_date")
    new_job.scheduled_end_time = data.get("scheduled_end_time")
    new_job.vehicle = data.get("vehicle")
    new_job.driver = data.get("driver")
    new_job.status = "Scheduled"
    
    team = data.get("team_members")
    if team:
        for member in team:
            new_job.append("team_members", {"employee": member})
            
    new_job.insert(ignore_permissions=True)
    
    # 2. Update the Job Card Status if it is NOT Reoccurring
    if job_card.is_reoccurring_quote != "YES":
        job_card.status = "Assigned"
        job_card.save(ignore_permissions=True)
        
    return "OK"

@frappe.whitelist()
def cancel_job_card(job_id):
    frappe.db.set_value("Enviro Job Card", job_id, "status", "Cancelled")
    return "OK"
