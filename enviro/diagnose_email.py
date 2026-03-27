import frappe

def execute():
    print("--- DIAGNOSTIC: EMAIL QUEUE & SCHEDULER ---")
    
    # 1. Check Scheduler Status
    try:
        from frappe.utils.scheduler import is_scheduler_inactive
        scheduler_inactive = is_scheduler_inactive()
        print(f"Scheduler Configured: {'DISABLED' if scheduler_inactive else 'ENABLED'}")
    except Exception as e:
        print("Could not verify scheduler status directly.")

    # 2. Check Default Outgoing Email Account
    email_accounts = frappe.get_all("Email Account", filters={"enable_outgoing": 1}, fields=["name", "email_id", "default_outgoing"])
    if not email_accounts:
        print("CRITICAL: No active Outgoing Email Account configured in the system.")
    else:
        print(f"Found {len(email_accounts)} outgoing email account(s):")
        for acc in email_accounts:
            print(f"- {acc.name} ({acc.email_id}) | Default: {'Yes' if acc.default_outgoing else 'No'}")
    
    # 3. Check specific Error Logs from the Email Queue
    last_queued = frappe.get_all("Email Queue", filters={"status": "Not Sent"}, fields=["name", "error"], order_by="creation desc", limit=1)
    if last_queued:
        q = last_queued[0]
        print(f"\nMost recent stuck email (Queue ID: {q.name}):")
        print(f"Error Stack Trace: {q.error if q.error else 'No error recorded. Waiting for scheduler.'}")

