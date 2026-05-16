import frappe
from frappe import _  # 1. ADDED: The translation function import


@frappe.whitelist()
def get_scheduling_data(from_date=None, to_date=None):
	"""
	Fetches data required for the Scheduling Dashboard:
	1. Queue Jobs: Approved Job Cards ready for scheduling.
	2. Scheduled Jobs: Jobs already allocated/scheduled within the date range.
	3. Vehicle Information: Available vehicles for allocation.
	"""
	# Only fetch jobs where the attached quote has completely bypassed/passed Accounts
	valid_job_ids = frappe.get_all(
		"Quotation",
		filters={"docstatus": ["<", 2], "custom_accounts_approval_status": "Approved"},
		pluck="custom_enviro_job_card",
	)

	base_filters = [["docstatus", "<", 2]]
	if valid_job_ids:
		base_filters.append(["name", "in", valid_job_ids])
	else:
		base_filters.append(["name", "=", "NONE_AUTHORIZED"])

	# Queue Jobs = Master Requests that aren't purely scheduled one-offs
	today = frappe.utils.today()
	queue_jobs = frappe.get_all(
		"Enviro Job Card",
		fields=[
			"name",
			"customer",
			"driver",
			"vehicle",
			"scheduled_start_date",
			"scheduled_start_time",
			"status",
			"is_reoccurring_quote",
			"is_outsourced_job",
			"frequency_in_weeks",
			"job_card_type",
			"source_quotation",
			"custom_last_scheduled_date",
		],
		filters=base_filters,
		or_filters=[
			["is_reoccurring_quote", "!=", "YES"],
			["custom_last_scheduled_date", "!=", today],
			["custom_last_scheduled_date", "is", "not set"],
		],
	)

	# Optimize Waste Type lookup using bulk query
	source_quotations = list(set([job.source_quotation for job in queue_jobs if job.source_quotation]))
	waste_map = {}
	if source_quotations:
		# Use optimized SQL to aggregate waste types per quotation
		items = frappe.db.sql(
			"""
			SELECT parent, GROUP_CONCAT(DISTINCT custom_waste_type ORDER BY custom_waste_type SEPARATOR ', ') as waste_types
			FROM `tabQuotation Item`
			WHERE parent IN %s AND custom_waste_type IS NOT NULL AND custom_waste_type != ''
			GROUP BY parent
			""",
			(source_quotations,),
			as_dict=True,
		)
		waste_map = {item.parent: item.waste_types for item in items}

	for job in queue_jobs:
		job.waste_type_label = waste_map.get(job.source_quotation) or (
			"Standard" if job.source_quotation else "Manual Job"
		)

	# Fetch Existing Scheduled Jobs within the timeline
	scheduled_filters = {"status": ["!=", "Cancelled"]}
	if from_date and to_date:
		scheduled_filters["scheduled_start_date"] = ["between", [from_date, to_date]]
	elif from_date:
		scheduled_filters["scheduled_start_date"] = [">=", from_date]
	elif to_date:
		scheduled_filters["scheduled_start_date"] = ["<=", to_date]

	scheduled_jobs = frappe.get_all(
		"Enviro Job",
		filters=scheduled_filters,
		fields=[
			"name",
			"customer",
			"driver",
			"vehicle",
			"scheduled_start_date",
			"scheduled_start_time",
			"status",
		],
	)

	vehicles = frappe.get_all("Vehicle", fields=["name", "license_plate"])

	return {"queue_jobs": queue_jobs, "scheduled_jobs": scheduled_jobs, "vehicles": vehicles}


def check_resource_availability(driver, vehicle, date, exclude_job=None, exclude_quote=None):
	"""
	Centralized validation to prevent double-booking of drivers or vehicles.
	Checks both 'Enviro Job' and 'Quotation' (intended schedules).
	"""
	if not date:
		return

	# 1. Check existing Enviro Jobs
	if driver:
		conflict = frappe.db.exists(
			"Enviro Job",
			{
				"driver": driver,
				"scheduled_start_date": date,
				"status": ["!=", "Cancelled"],
				"name": ["!=", exclude_job] if exclude_job else ["is", "set"],
			},
		)
		if conflict:
			frappe.throw(
				_("Driver {0} is already scheduled for Job {1} on {2}").format(driver, conflict, date)
			)

	if vehicle:
		conflict = frappe.db.exists(
			"Enviro Job",
			{
				"vehicle": vehicle,
				"scheduled_start_date": date,
				"status": ["!=", "Cancelled"],
				"name": ["!=", exclude_job] if exclude_job else ["is", "set"],
			},
		)
		if conflict:
			frappe.throw(
				_("Vehicle {0} is already scheduled for Job {1} on {2}").format(vehicle, conflict, date)
			)

	# 2. Check intended schedules in Quotations (pending reoccurring)
	if driver:
		conflict = frappe.db.exists(
			"Quotation",
			{
				"custom_intended_driver": driver,
				"custom_intended_start_date": date,
				"docstatus": ["<", 2],
				"status": ["not in", ["Cancelled", "Lost"]],
				"name": ["!=", exclude_quote] if exclude_quote else ["is", "set"],
			},
		)
		if conflict:
			frappe.throw(
				_("Driver {0} is already reserved for Quotation {1} on {2}").format(driver, conflict, date)
			)

	if vehicle:
		conflict = frappe.db.exists(
			"Quotation",
			{
				"custom_intended_vehicle": vehicle,
				"custom_intended_start_date": date,
				"docstatus": ["<", 2],
				"status": ["not in", ["Cancelled", "Lost"]],
				"name": ["!=", exclude_quote] if exclude_quote else ["is", "set"],
			},
		)
		if conflict:
			frappe.throw(
				_("Vehicle {0} is already reserved for Quotation {1} on {2}").format(vehicle, conflict, date)
			)


@frappe.whitelist()
# 2. ADDED: Type hints (str) for job_id and payload
def api_schedule_job(job_id: str, payload: str):
	"""
	Main entry point for scheduling a Job Card.
	Handles both One-Off (direct) and Reoccurring (approval pipeline) jobs.
	"""
	import json

	data = json.loads(payload)

	# PRE-CHECK Availability
	check_resource_availability(data.get("driver"), data.get("vehicle"), data.get("scheduled_start_date"))

	job_card = frappe.get_doc("Enviro Job Card", job_id)

	# --- CASE 1: REOCCURRING JOB (Approval Pipeline) ---
	if job_card.is_reoccurring_quote == "YES":
		if not job_card.source_quotation:
			# 3. ADDED: Wrapped the string in _() for translation
			frappe.throw(_("Master Job Card has no source quotation to clone."))

		# 1. Clone the Master Quotation
		master_quote = frappe.get_doc("Quotation", job_card.source_quotation)
		new_quote = frappe.copy_doc(master_quote)
		new_quote.transaction_date = frappe.utils.today()
		new_quote.custom_enviro_job_card = job_card.name

		# 2. Store the 'Intended Schedule' payload
		new_quote.custom_intended_start_date = data.get("scheduled_start_date")
		new_quote.custom_intended_start_time = data.get("scheduled_start_time")
		new_quote.custom_intended_end_date = data.get("scheduled_end_date")
		new_quote.custom_intended_end_time = data.get("scheduled_end_time")
		new_quote.custom_intended_vehicle = data.get("vehicle")
		new_job_driver = data.get("driver")
		new_quote.custom_intended_driver = new_job_driver
		new_quote.custom_intended_team = json.dumps(data.get("team_members") or [])

		# 3. Reset workflow status
		new_quote.custom_client_approval_status = "Pending"
		new_quote.custom_accounts_approval_status = "Pending"

		new_quote.insert(ignore_permissions=True)

		# 4. CREATE ENVIRO JOB IMMEDIATELY (Status: Allocated)
		# This ensures the dashboard shows a Job ID instead of a Quote ID
		new_job = frappe.new_doc("Enviro Job")
		new_job.source_job_card = job_card.name
		new_job.quotation = new_quote.name
		new_job.customer = job_card.customer
		new_job.site = job_card.site
		new_job.scheduled_start_date = data.get("scheduled_start_date")
		new_job.scheduled_start_time = data.get("scheduled_start_time")
		new_job.scheduled_end_date = data.get("scheduled_end_date")
		new_job.scheduled_end_time = data.get("scheduled_end_time")
		new_job.vehicle = data.get("vehicle")
		new_job.driver = data.get("driver")
		new_job.custom_waste_type = job_card.custom_waste_type
		new_job.status = "Allocated"

		team = data.get("team_members")
		if team:
			for member in team:
				new_job.append("team_members", {"employee": member})

		new_job.insert(ignore_permissions=True)

		# 5. Filter logic: Mark Master as 'Scheduled Today' so it hides from DB
		job_card.custom_last_scheduled_date = frappe.utils.today()
		job_card.save(ignore_permissions=True)

		# 6. Global Action: Removed auto-trigger email logic since it's now manual via the button.
		return {"status": "OK", "type": "reoccurring", "quote": new_quote.name, "job": new_job.name}

	# --- CASE 2: ONE-OFF JOB (Direct Scheduling) ---
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
	new_job.custom_waste_type = job_card.custom_waste_type
	new_job.status = "Scheduled"

	team = data.get("team_members")
	if team:
		for member in team:
			new_job.append("team_members", {"employee": member})

	new_job.insert(ignore_permissions=True)

	# Update the Job Card Status
	job_card.status = "Assigned"
	job_card.save(ignore_permissions=True)

	return {"status": "OK", "type": "one-off", "job": new_job.name}


@frappe.whitelist()
# 4. ADDED: Type hint for cancel function
def cancel_job_card(job_id: str):
	"""
	If Reoccurring: 'Skips' this occurrence by hiding it from the queue today.
	If One-Off: Permanently Archives/Cancels the Job Card.
	"""
	is_reoccurring = frappe.db.get_value("Enviro Job Card", job_id, "is_reoccurring_quote")

	if is_reoccurring == "YES":
		# Skip this occurrence (hides it from scheduling queue until next cycle)
		frappe.db.set_value("Enviro Job Card", job_id, "custom_last_scheduled_date", frappe.utils.today())
		return "Skipped"
	else:
		# Standard permanent cancellation
		frappe.db.set_value("Enviro Job Card", job_id, "status", "Cancelled")
		return "Cancelled"


def _get_busy_resources(date: str, resource_type: str) -> set:
	"""Helper to get busy drivers or vehicles for a given date"""
	if resource_type == "driver":
		job_field, quote_field = "driver", "custom_intended_driver"
	else:
		job_field, quote_field = "vehicle", "custom_intended_vehicle"

	busy_jobs = frappe.get_all(
		"Enviro Job",
		filters={"scheduled_start_date": date, "status": ["!=", "Cancelled"]},
		fields=[job_field],
	)

	busy_quotes = frappe.get_all(
		"Quotation",
		filters={
			"custom_intended_start_date": date,
			"docstatus": ["<", 2],
			"status": ["not in", ["Cancelled", "Lost"]],
		},
		fields=[quote_field],
	)

	busy_resources = {j.get(job_field) for j in busy_jobs if j.get(job_field)}
	busy_resources.update(q.get(quote_field) for q in busy_quotes if q.get(quote_field))

	return busy_resources


@frappe.whitelist()
# 5. ADDED: Type hints for the query function
def get_driver_employees(
	doctype: str, txt: str, searchfield: str, start: int, page_len: int, filters: dict | None = None
):
	"""Standard search query for drivers, excluding those busy on the selected date."""
	valid_roles = [
		"Driver Factory Hand (Web)",
		"Driver Factory Hand (Mobile)",
		"Driver Liquid Waste Technician (Web)",
		"Driver Liquid Waste Technician (Mobile)",
	]

	user_emails = frappe.get_all("Has Role", filters={"role": ["in", valid_roles]}, pluck="parent")
	user_emails = list(set(user_emails))

	if not user_emails:
		return []

	conditions = {"user_id": ["in", user_emails], "status": "Active"}

	# FILTER BY DATE AVAILABILITY
	date = filters.get("date") if filters else None
	if date:
		busy_drivers = _get_busy_resources(date, "driver")
		if busy_drivers:
			conditions["name"] = ["not in", list(busy_drivers)]

	employees = frappe.get_all("Employee", filters=conditions, fields=["name", "employee_name"])

	result = []
	safe_txt = (txt or "").lower()
	for emp in employees:
		if safe_txt in emp.name.lower() or safe_txt in str(emp.employee_name or "").lower():
			result.append([emp.name, emp.employee_name or ""])

	return result


@frappe.whitelist()
def get_available_vehicles(
	doctype: str, txt: str, searchfield: str, start: int, page_len: int, filters: dict | None = None
):
	"""Standard search query for vehicles, excluding those busy on the selected date."""
	conditions = {}

	# FILTER BY DATE AVAILABILITY
	date = filters.get("date") if filters else None
	if date:
		busy_vehicles = _get_busy_resources(date, "vehicle")
		if busy_vehicles:
			conditions["name"] = ["not in", list(busy_vehicles)]

	vehicles = frappe.get_all("Vehicle", filters=conditions, fields=["name", "license_plate"])

	result = []
	safe_txt = (txt or "").lower()
	for v in vehicles:
		if safe_txt in v.name.lower() or safe_txt in str(v.license_plate or "").lower():
			result.append([v.name, v.license_plate or ""])

	return result
