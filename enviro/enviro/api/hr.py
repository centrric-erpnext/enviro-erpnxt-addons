import frappe
from frappe import _
from frappe.utils import getdate, today


def _check_hr_access():
	"""
	Centralized role check for HR actions.
	Authorized roles: Administrator, Superadmin, System Manager, Manager, HR Manager, Accounts Manager, Director.
	"""
	roles = frappe.get_roles(frappe.session.user)
	allowed = (
		"Administrator",
		"Superadmin",
		"System Manager",
		"Manager",
		"HR Manager",
		"Accounts Manager",
		"Director",
	)
	if not any(r in roles for r in allowed):
		frappe.throw(
			_("Not permitted: You do not have the required role to perform HR actions."),
			frappe.PermissionError,
		)


@frappe.whitelist()
def get_leave_applications():
	"""
	Return all leave applications with employee info and attachment status.
	Results are cached for 2 minutes to reduce DB load.
	"""
	_check_hr_access()

	cache_key = f"hr_leave_applications_{frappe.session.user}"
	cached = frappe.cache().get_value(cache_key)
	if cached:
		return cached

	leaves = frappe.get_all(
		"Leave Application",
		fields=[
			"name",
			"employee",
			"employee_name",
			"from_date",
			"to_date",
			"leave_type",
			"status",
			"description",
			"docstatus",
		],
		order_by="creation desc",
		limit=100,
	)

	if not leaves:
		return []

	# Bulk fetch employee photos
	employee_names = list(set(l.employee for l in leaves))
	photos_map = {
		d.name: d.image
		for d in frappe.get_all(
			"Employee", filters={"name": ["in", employee_names]}, fields=["name", "image"]
		)
	}

	# Bulk fetch jobs for the period
	# We'll fetch all jobs for these employees that overlap the date range of the leaves
	# For simplicity and performance, we fetch all jobs for these employees in the range
	min_date = min(l.from_date for l in leaves)
	max_date = max(l.to_date for l in leaves)

	jobs = frappe.get_all(
		"Enviro Job",
		filters={
			"driver": ["in", employee_names],
			"scheduled_start_date": ["between", [min_date, max_date]],
			"status": ["!=", "Cancelled"],
		},
		fields=["name", "driver", "scheduled_start_date"],
	)

	jobs_map = {}
	for j in jobs:
		if j.driver not in jobs_map:
			jobs_map[j.driver] = []
		jobs_map[j.driver].append(j)

	# Bulk fetch attachments
	leave_names = [l.name for l in leaves]
	attachments = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Leave Application", "attached_to_name": ["in", leave_names]},
		fields=["attached_to_name", "file_url"],
	)
	attachment_map = {}
	for a in attachments:
		if a.attached_to_name not in attachment_map:
			attachment_map[a.attached_to_name] = []
		attachment_map[a.attached_to_name].append(a.file_url)

	results = []
	for leave in leaves:
		photo = photos_map.get(leave.employee) or ""

		# Filter jobs for this specific leave period
		relevant_jobs = [
			j.name
			for j in jobs_map.get(leave.employee, [])
			if leave.from_date <= j.scheduled_start_date <= leave.to_date
		]
		assigned_jobs = ", ".join(relevant_jobs[:5]) if relevant_jobs else "No Jobs Assigned."

		results.append(
			{
				"name": leave.name,
				"employee": leave.employee,
				"employee_name": leave.employee_name,
				"photo": photo,
				"from_date": frappe.utils.formatdate(leave.from_date),
				"to_date": frappe.utils.formatdate(leave.to_date),
				"leave_type": leave.leave_type,
				"status": leave.status,
				"docstatus": leave.docstatus,
				"assigned_jobs": assigned_jobs,
				"attachments": attachment_map.get(leave.name, []),
			}
		)

	frappe.cache().set_value(cache_key, results, expires_in_sec=120)
	return results


@frappe.whitelist()
def get_timesheets():
	"""
	Return all Enviro Weekly Timesheets for admin review.
	Results are cached for 2 minutes.
	"""
	_check_hr_access()

	cache_key = f"hr_timesheets_{frappe.session.user}"
	cached = frappe.cache().get_value(cache_key)
	if cached:
		return cached

	from datetime import timedelta

	sheets = frappe.get_all(
		"Enviro Weekly Timesheet",
		fields=[
			"name",
			"employee",
			"employee_name",
			"week_beginning",
			"status",
			"docstatus",
			"timesheet_approver",
			"modified",
		],
		order_by="creation desc",
		limit=100,
	)

	if not sheets:
		return []

	# Bulk fetch photos
	employee_names = list(set(ts.employee for ts in sheets))
	photos_map = {
		d.name: d.image
		for d in frappe.get_all(
			"Employee", filters={"name": ["in", employee_names]}, fields=["name", "image"]
		)
	}

	results = []
	for ts in sheets:
		photo = photos_map.get(ts.employee) or ""
		week_end = ts.week_beginning + timedelta(days=6) if ts.week_beginning else None
		results.append(
			{
				"name": ts.name,
				"employee": ts.employee,
				"employee_name": ts.employee_name,
				"photo": photo,
				"week_beginning": frappe.utils.formatdate(ts.week_beginning),
				"week_end": frappe.utils.formatdate(week_end) if week_end else "",
				"last_updated": frappe.utils.formatdate(ts.modified),
				"status": ts.status or "Pending",
				"docstatus": ts.docstatus,
				"timesheet_approver": ts.timesheet_approver or "",
			}
		)

	frappe.cache().set_value(cache_key, results, expires_in_sec=120)
	return results


def _update_doc_state(doctype, name, status, cache_key_prefix):
	_check_hr_access()
	doc = frappe.get_doc(doctype, name)

	if status == "Approved":
		if doc.docstatus == 0:
			doc.status = "Approved"
			doc.save(ignore_permissions=True)
			doc.submit()
		elif doc.docstatus == 1:
			doc.db_set("status", "Approved")
	elif status == "Rejected":
		if doc.docstatus == 0:
			doc.status = "Rejected"
			doc.save(ignore_permissions=True)
		elif doc.docstatus == 1:
			frappe.db.set_value(doctype, name, "status", "Rejected")
	elif status == "Cancelled":
		if doc.docstatus == 1:
			doc.cancel()
		frappe.db.set_value(doctype, name, "status", "Cancelled")

	frappe.cache().delete_value(f"{cache_key_prefix}_{frappe.session.user}")
	return status


@frappe.whitelist()
def approve_leave(name):
	return _update_doc_state("Leave Application", name, "Approved", "hr_leave_applications")


@frappe.whitelist()
def reject_leave(name):
	return _update_doc_state("Leave Application", name, "Rejected", "hr_leave_applications")


@frappe.whitelist()
def delete_leave(name):
	return _update_doc_state("Leave Application", name, "Cancelled", "hr_leave_applications")


@frappe.whitelist()
def approve_timesheet(name):
	return _update_doc_state("Enviro Weekly Timesheet", name, "Approved", "hr_timesheets")


@frappe.whitelist()
def reject_timesheet(name):
	return _update_doc_state("Enviro Weekly Timesheet", name, "Rejected", "hr_timesheets")


@frappe.whitelist()
def delete_timesheet(name):
	return _update_doc_state("Enviro Weekly Timesheet", name, "Cancelled", "hr_timesheets")
