import frappe
from frappe.utils import now_datetime, today


@frappe.whitelist()
def get_home_dashboard_data():
	"""
	Combines notifications, jobs, and schedule data for the Home Workspace.
	"""
	return {
		"notifications": get_recent_activities(),
		"all_jobs": get_all_jobs_summary(),
		"todays_schedule": get_todays_appointments(),
	}


def get_recent_activities():
	"""
	Fetches the last 6 activities based on status changes.
	Matches strings like 'Quote reviewed', 'Quote approved', 'Quotation Created'.
	"""
	activities = []

	# Target status keywords provided by user
	target_messages = ["Quote reviewed", "Quote approved", "Quotation Created"]

	# 1. Search in Activity Log (Standard Frappe Audit Log equivalent)
	# Most likely place for automated status updates
	logs = frappe.get_all(
		"Activity Log",
		fields=["name", "subject", "creation", "reference_doctype", "reference_name"],
		filters=[["subject", "like", "%Quote%"], ["reference_doctype", "=", "Quotation"]],
		limit=20,
		order_by="creation desc",
	)

	for log in logs:
		# Check if the message matches target statuses
		if any(msg.lower() in str(log.subject).lower() for msg in target_messages):
			activities.append(
				{
					"id": log.name,
					"title": log.subject,
					"timestamp": log.creation,
					"doctype": log.reference_doctype,
					"docname": log.reference_name,
				}
			)

	# 2. Search in Communication (Timeline messages)
	if len(activities) < 6:
		comms = frappe.get_all(
			"Communication",
			fields=["name", "subject", "content", "creation", "reference_doctype", "reference_name"],
			filters=[["reference_doctype", "=", "Quotation"], ["communication_type", "=", "Comment"]],
			limit=20,
			order_by="creation desc",
		)
		for comm in comms:
			if any(msg.lower() in str(comm.content).lower() for msg in target_messages):
				activities.append(
					{
						"id": comm.name,
						"title": comm.subject or "Quotation Activity",
						"timestamp": comm.creation,
						"doctype": comm.reference_doctype,
						"docname": comm.reference_name,
					}
				)

	# Sort and slice
	activities = sorted(activities, key=lambda x: x["timestamp"], reverse=True)
	return activities[:6]


def get_all_jobs_summary():
	"""
	Returns latest Enviro Jobs with fields mapped for the Quick List.
	Code -> name
	Title -> customer (customer_name)
	Description -> site (site_name)
	"""
	jobs = frappe.get_all(
		"Enviro Job", fields=["name", "customer", "site", "status"], limit=10, order_by="creation desc"
	)

	# Enforce field mapping for frontend consistency
	result = []
	for job in jobs:
		customer_name = (
			frappe.db.get_value("Customer", job.customer, "customer_name") if job.customer else "N/A"
		)
		site_name = frappe.db.get_value("Site", job.site, "site_name") if job.site else "N/A"

		result.append(
			{"code": job.name, "title": customer_name, "description": site_name, "status": job.status}
		)
	return result


def get_todays_appointments():
	"""
	Fetches today's appointments for the 2x2 grid.
	"""
	current_date = today()
	appointments = frappe.get_all(
		"Enviro Job",
		fields=["name", "customer", "scheduled_start_time", "status"],
		filters={"scheduled_start_date": current_date},
		limit=4,
		order_by="scheduled_start_time asc",
	)

	# Polish formatting
	for appt in appointments:
		appt.customer_name = (
			frappe.db.get_value("Customer", appt.customer, "customer_name") if appt.customer else "N/A"
		)
		# Convert duration or just show time
		appt.time_label = str(appt.scheduled_start_time)

	return appointments
