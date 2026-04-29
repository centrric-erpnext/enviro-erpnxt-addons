import frappe
from frappe import _  # 1. ADDED: The translation function import


@frappe.whitelist()
def get_scheduling_data():
	# Only fetch jobs where the attached quote has completely bypassed/passed Accounts
	approved_quotes = frappe.get_all(
		"Quotation",
		filters={"docstatus": ["<", 2], "custom_accounts_approval_status": "Approved"},
		fields=["custom_enviro_job_card", "customer_name"],
	)

	valid_job_ids = [q.custom_enviro_job_card for q in approved_quotes if q.custom_enviro_job_card]

	filters = [["docstatus", "<", 2]]

	# Strict locking to approved quotes ONLY:
	if valid_job_ids:
		filters.append(["name", "in", valid_job_ids])
	else:
		# If no approved quotes exist, return an empty tracking list for extreme security
		filters.append(["name", "=", "NONE_AUTHORIZED"])

	# Queue Jobs = Master Requests that aren't purely scheduled one-offs
	# For Reoccurring: Only show if it hasn't been scheduled 'today' to keep the UI clean
	today = frappe.utils.today()

	base_filters = [["docstatus", "<", 2]]
	if valid_job_ids:
		base_filters.append(["name", "in", valid_job_ids])
	else:
		base_filters.append(["name", "=", "NONE_AUTHORIZED"])

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

	# Calculate Waste Type for Queue Jobs
	source_quotations = list(set([job.source_quotation for job in queue_jobs if job.source_quotation]))
	waste_map = {}
	if source_quotations:
		items = frappe.db.sql(
			"""
			SELECT parent, custom_waste_type
			FROM `tabQuotation Item`
			WHERE parent IN %s AND custom_waste_type IS NOT NULL AND custom_waste_type != ''
			""",
			(source_quotations,),
			as_dict=True,
		)
		for item in items:
			if item.parent not in waste_map:
				waste_map[item.parent] = set()
			waste_map[item.parent].add(item.custom_waste_type)

	for job in queue_jobs:
		if job.source_quotation:
			w_types = waste_map.get(job.source_quotation)
			if w_types:
				job.waste_type_label = ", ".join(sorted(list(w_types)))
			else:
				job.waste_type_label = "Standard"
		else:
			job.waste_type_label = "Manual Job"

	# Scheduled Jobs = Physical executions on the calendar
	scheduled_jobs = frappe.get_all(
		"Enviro Job",
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

	# Fetch Pending Reoccurring Schedules (Quotations with intended dates)
	pending_quotes = frappe.get_all(
		"Quotation",
		filters={
			"docstatus": ["<", 2],
			"custom_intended_start_date": ["is", "set"],
			"custom_accounts_approval_status": ["!=", "Approved"],  # If not approved yet, it is still pending
		},
		fields=[
			"name",
			"customer_name as customer",
			"custom_intended_driver as driver",
			"custom_intended_vehicle as vehicle",
			"custom_intended_start_date as scheduled_start_date",
			"custom_intended_start_time as scheduled_start_time",
			"status",
		],
	)

	# Mark quotations as pending for the frontend
	for q in pending_quotes:
		q.is_pending = True
		scheduled_jobs.append(q)

	vehicles = frappe.get_all("Vehicle", fields=["name", "license_plate"])

	return {"queue_jobs": queue_jobs, "scheduled_jobs": scheduled_jobs, "vehicles": vehicles}


def check_resource_availability(driver, vehicle, date, exclude_job=None, exclude_quote=None):
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
		if new_quote.custom_requires_client_approval == 1:
			new_quote.custom_client_approval_status = "Pending"
			new_quote.custom_accounts_approval_status = ""
		else:
			new_quote.custom_client_approval_status = "Not Required"
			new_quote.custom_accounts_approval_status = "Pending"

		new_quote.insert(ignore_permissions=True)

		# 4. Filter logic: Mark Master as 'Scheduled Today' so it hides from DB
		job_card.custom_last_scheduled_date = frappe.utils.today()
		job_card.save(ignore_permissions=True)

		# 5. Global Action: Trigger Email if needed
		if new_quote.custom_requires_client_approval == 1:
			from enviro.custom_scripts.quotation import send_approval_email

			send_approval_email(new_quote.name)

		return {"status": "OK", "type": "reoccurring", "quote": new_quote.name}

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
	frappe.db.set_value("Enviro Job Card", job_id, "status", "Cancelled")
	return "OK"


@frappe.whitelist()
# 5. ADDED: Type hints for the query function
def get_driver_employees(
	doctype: str, txt: str, searchfield: str, start: int, page_len: int, filters: dict | None = None
):
	valid_roles = [
		"Driver Factory Hand (Web)",
		"Driver Factory Hand (Mobile)",
		"Driver Liquid Waste Technician (Web)",
		"Driver Liquid Waste Technician (Mobile)",
	]

	users = frappe.get_all("Has Role", filters={"role": ["in", valid_roles]}, fields=["parent"])
	user_emails = list(set([u.parent for u in users]))

	if not user_emails:
		return []

	conditions = {"user_id": ["in", user_emails], "status": "Active"}

	# FILTER BY DATE AVAILABILITY
	date = filters.get("date") if filters else None
	if date:
		# Drivers with Jobs
		busy_jobs = frappe.get_all(
			"Enviro Job",
			filters={"scheduled_start_date": date, "status": ["!=", "Cancelled"]},
			fields=["driver"],
		)
		# Drivers with Reservations (Quotations)
		busy_quotes = frappe.get_all(
			"Quotation",
			filters={
				"custom_intended_start_date": date,
				"docstatus": ["<", 2],
				"status": ["not in", ["Cancelled", "Lost"]],
			},
			fields=["custom_intended_driver"],
		)

		busy_drivers = set([j.driver for j in busy_jobs if j.driver])
		busy_drivers.update([q.custom_intended_driver for q in busy_quotes if q.custom_intended_driver])

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
	conditions = {}

	# FILTER BY DATE AVAILABILITY
	date = filters.get("date") if filters else None
	if date:
		# Vehicles with Jobs
		busy_jobs = frappe.get_all(
			"Enviro Job",
			filters={"scheduled_start_date": date, "status": ["!=", "Cancelled"]},
			fields=["vehicle"],
		)
		# Vehicles with Reservations (Quotations)
		busy_quotes = frappe.get_all(
			"Quotation",
			filters={
				"custom_intended_start_date": date,
				"docstatus": ["<", 2],
				"status": ["not in", ["Cancelled", "Lost"]],
			},
			fields=["custom_intended_vehicle"],
		)

		busy_vehicles = set([j.vehicle for j in busy_jobs if j.vehicle])
		busy_vehicles.update([q.custom_intended_vehicle for q in busy_quotes if q.custom_intended_vehicle])

		if busy_vehicles:
			conditions["name"] = ["not in", list(busy_vehicles)]

	vehicles = frappe.get_all("Vehicle", filters=conditions, fields=["name", "license_plate"])

	result = []
	safe_txt = (txt or "").lower()
	for v in vehicles:
		if safe_txt in v.name.lower() or safe_txt in str(v.license_plate or "").lower():
			result.append([v.name, v.license_plate or ""])

	return result
