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

	results = []
	for leave in leaves:
		# Get employee photo
		photo = frappe.db.get_value("Employee", leave.employee, "image", cache=True) or ""

		# Check for assigned jobs overlapping the leave period
		try:
			jobs = frappe.get_all(
				"Enviro Job",
				filters={
					"driver": leave.employee,
					"scheduled_start_date": ["between", [leave.from_date, leave.to_date]],
				},
				pluck="name",
				limit=5,
			)
			assigned_jobs = ", ".join(jobs) if jobs else "No Jobs Assigned."
		except Exception:
			assigned_jobs = "No Jobs Assigned."

		# Check for file attachments
		attachments = frappe.get_all(
			"File",
			filters={"attached_to_doctype": "Leave Application", "attached_to_name": leave.name},
			pluck="file_url",
		)

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
				"attachments": attachments,
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

	results = []
	for ts in sheets:
		photo = frappe.db.get_value("Employee", ts.employee, "image", cache=True) or ""
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


@frappe.whitelist()
def approve_leave(name):
	"""
	Approve a leave application.
	Submits the document and updates status.
	"""
	_check_hr_access()
	doc = frappe.get_doc("Leave Application", name)
	if doc.docstatus == 0:
		doc.status = "Approved"
		doc.save(ignore_permissions=True)
		doc.submit()
	elif doc.docstatus == 1:
		doc.db_set("status", "Approved")

	frappe.cache().delete_value(f"hr_leave_applications_{frappe.session.user}")
	return "Approved"


@frappe.whitelist()
def reject_leave(name):
	"""
	Reject a leave application by updating its status.
	"""
	_check_hr_access()
	doc = frappe.get_doc("Leave Application", name)
	if doc.docstatus == 0:
		doc.status = "Rejected"
		doc.save(ignore_permissions=True)
	elif doc.docstatus == 1:
		frappe.db.set_value("Leave Application", name, "status", "Rejected")

	frappe.cache().delete_value(f"hr_leave_applications_{frappe.session.user}")
	return "Rejected"


@frappe.whitelist()
def delete_leave(name):
	"""
	Cancel a leave application and keep it in the list (marked as Cancelled).
	"""
	_check_hr_access()
	doc = frappe.get_doc("Leave Application", name)
	if doc.docstatus == 1:
		doc.cancel()

	frappe.db.set_value("Leave Application", name, "status", "Cancelled")
	frappe.cache().delete_value(f"hr_leave_applications_{frappe.session.user}")
	return "Cancelled"


@frappe.whitelist()
def approve_timesheet(name):
	"""
	Approve and submit an Enviro Weekly Timesheet.
	"""
	_check_hr_access()
	doc = frappe.get_doc("Enviro Weekly Timesheet", name)
	if doc.docstatus == 0:
		doc.status = "Approved"
		doc.save(ignore_permissions=True)
		doc.submit()
	elif doc.docstatus == 1:
		doc.db_set("status", "Approved")

	frappe.cache().delete_value(f"hr_timesheets_{frappe.session.user}")
	return "Approved"


@frappe.whitelist()
def reject_timesheet(name):
	"""
	Cancel and mark an Enviro Weekly Timesheet as Rejected.
	"""
	_check_hr_access()
	doc = frappe.get_doc("Enviro Weekly Timesheet", name)
	if doc.docstatus == 1:
		doc.cancel()
	frappe.db.set_value("Enviro Weekly Timesheet", name, "status", "Rejected")
	frappe.cache().delete_value(f"hr_timesheets_{frappe.session.user}")
	return "Rejected"


@frappe.whitelist()
def delete_timesheet(name):
	"""
	Cancel an Enviro Weekly Timesheet and keep it in the list (marked as Cancelled).
	"""
	_check_hr_access()
	doc = frappe.get_doc("Enviro Weekly Timesheet", name)
	if doc.docstatus == 1:
		doc.cancel()

	frappe.db.set_value("Enviro Weekly Timesheet", name, "status", "Cancelled")
	frappe.cache().delete_value(f"hr_timesheets_{frappe.session.user}")
	return "Cancelled"
