import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import now_datetime, today

from enviro.enviro.utils.response_handler import ResponseHandler


def get_request_params():
	"""Helper to get parameters from form-data or JSON body"""
	params = frappe.form_dict.copy()
	if frappe.request.json:
		params.update(frappe.request.json)
	return params


@frappe.whitelist()
def get_driver_context():
	"""Returns the current driver's employee record and basic stats"""
	try:
		user = frappe.session.user
		employee = frappe.db.get_value(
			"Employee", {"user_id": user}, ["name", "employee_name", "designation"], as_dict=True
		)

		if not employee:
			frappe.throw(_("No Employee record linked to user {0}").format(user), title=_("User Not Found"))

		# Check if vehicle check for today is done
		vpi_done = frappe.db.exists(
			"Vehicle Pre-Inspection Check", {"driver": employee.name, "date": [">=", today()]}
		)

		ResponseHandler.success({"employee": employee, "vpi_done": bool(vpi_done)})
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_driver_context API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_assigned_jobs():
	"""Returns all 'Scheduled', 'In Transit', or 'On Site' jobs for the current driver"""
	try:
		user = frappe.session.user
		employee_name = frappe.db.get_value("Employee", {"user_id": user}, "name")

		if not employee_name:
			ResponseHandler.success([])
			return

		jobs = frappe.get_all(
			"Enviro Job",
			filters={"driver": employee_name, "status": ["in", ["Scheduled", "In Transit", "On Site"]]},
			fields=[
				"name",
				"customer",
				"site",
				"scheduled_start_date",
				"scheduled_start_time",
				"status",
				"vehicle",
			],
		)

		ResponseHandler.success(jobs)
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_assigned_jobs API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist(methods=["POST"])
def update_job_status():
	"""Mobile-friendly wrapper for job state transitions (Supports JSON body)"""
	try:
		params = get_request_params()
		job_name = params.get("job_name")
		action = params.get("action")

		if not job_name or not action:
			frappe.throw(_("Missing 'job_name' or 'action' parameter."), title=_("Missing Information"))

		from enviro.enviro.doctype.enviro_job.enviro_job import (
			arrive_at_depot,
			arrive_at_facility,
			depart_depot,
			depart_facility,
			finish_job,
			start_job,
		)

		result = None
		timestamp = params.get("timestamp")

		if action == "depart_facility":
			result = depart_facility(job_name, timestamp)
		elif action == "start":
			# start_job(job_id, pre_image=None)
			result = start_job(job_name, params.get("pre_job_image"))
		elif action == "finish":
			# finish_job(job_id, post_image=None, signature=None)
			result = finish_job(job_name, params.get("post_job_image"), params.get("contact_signature"))
		elif action == "arrive_depot":
			result = arrive_at_depot(job_name, timestamp)
		elif action == "depart_depot":
			result = depart_depot(job_name, timestamp)
		elif action == "arrive_facility":
			result = arrive_at_facility(job_name, timestamp)
		else:
			frappe.throw(_("Invalid action: {0}").format(action), title=_("Invalid Action"))

		ResponseHandler.success(result)

	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="update_job_status API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist(methods=["POST"])
def submit_vehicle_checklist():
	"""Submit a Vehicle Pre-Inspection Check from mobile (Supports JSON body)"""
	try:
		params = get_request_params()

		user = frappe.session.user
		employee_name = frappe.db.get_value("Employee", {"user_id": user}, "name")

		if not employee_name:
			frappe.throw(_("Employee record not found for user."), title=_("User Not Found"))

		# Create the VPI record
		vpi = frappe.new_doc("Vehicle Pre-Inspection Check")
		vpi.update(params)
		vpi.driver = employee_name
		vpi.date = now_datetime()
		vpi.insert(ignore_permissions=True)
		vpi.submit()

		# Explicitly trigger the fault reporting logic for the mobile app
		faults = str(params.get("any_fault_to_report", ""))
		is_fault = faults in ["1", "true", "True"]
		message = "Checklist submitted successfully."

		if is_fault:
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"description": f"URGENT: Vehicle {vpi.vehicle} reported faults on {vpi.date} by {vpi.driver}.",
					"reference_type": "Vehicle Pre-Inspection Check",
					"reference_name": vpi.name,
					"assigned_by": vpi.driver,
				}
			).insert(ignore_permissions=True)
			message = (
				"Checklist submitted. ⚠️ A fault report has been automatically sent to the management team."
			)

		ResponseHandler.success({"vpi_name": vpi.name, "message": message, "fault_reported": is_fault})
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="submit_vehicle_checklist API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_all_drivers():
	"""Returns a list of all active drivers based on Driver Roles"""
	try:
		valid_roles = [
			"Driver Factory Hand (Mobile)",
			"Driver Factory Hand (Web)",
			"Driver Liquid Waste Technician (Mobile)",
			"Driver Liquid Waste Technician (Web)",
		]

		# Find all User IDs that have these roles
		user_ids = frappe.get_all("Has Role", filters={"role": ["in", valid_roles]}, pluck="parent")
		user_ids = list(set(user_ids))

		if not user_ids:
			ResponseHandler.success([])
			return

		# Fetch Active Employees linked to these users
		drivers = frappe.get_all(
			"Employee",
			filters={"status": "Active", "user_id": ["in", user_ids]},
			fields=["name", "employee_name", "user_id"],
		)

		ResponseHandler.success(drivers)
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_all_drivers API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist(methods=["POST"])
def update_account_info():
	"""Unified API for updating Profile, Identity, and Security settings (Supports JSON body)"""
	try:
		params = get_request_params()
		user_id = frappe.session.user
		if user_id == "Guest":
			frappe.throw(_("Please login to update your account."), title=_("Authentication Required"))

		user = frappe.get_doc("User", user_id)

		# 1. Handle Security (Password)
		new_password = params.get("new_password")
		old_password = params.get("old_password")
		if new_password:
			if not old_password:
				frappe.throw(
					_("Current password is required to set a new password."), title=_("Missing Information")
				)

			# Verify old password
			from frappe.auth import LoginManager

			login_manager = LoginManager()
			login_manager.authenticate(user_id, old_password)

			# Update to new password
			from frappe.utils.password import update_password

			update_password(user_id, new_password)

		# 2. Handle Identity (Username)
		username = params.get("username")
		if username and username != user.username:
			if frappe.db.exists("User", {"username": username}):
				frappe.throw(
					_("Username '{0}' is already taken.").format(username), title=_("Username Unavailable")
				)
			user.username = username

		# 3. Handle Profile (Name, Phone, Bio, Image)
		full_name = params.get("full_name")
		mobile_no = params.get("mobile_no")
		user_image = params.get("user_image")
		bio = params.get("bio")

		if full_name:
			user.full_name = full_name
		if mobile_no:
			user.mobile_no = mobile_no
		if user_image:
			user.user_image = user_image
		if bio:
			user.bio = bio

		user.save(ignore_permissions=True)

		# 4. Sync Profile with Employee Record
		employee_name = frappe.db.get_value("Employee", {"user_id": user_id}, "name")
		if employee_name:
			emp = frappe.get_doc("Employee", employee_name)
			if full_name:
				emp.employee_name = full_name
			if mobile_no:
				emp.cell_number = mobile_no
			if user_image:
				emp.image = user_image
			emp.save(ignore_permissions=True)

		frappe.db.commit()  # ensure the writes are persisted if all went well

		ResponseHandler.success({"message": "Account info updated successfully."})
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="update_account_info API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_all_vehicles():
	"""Returns a list of all vehicles available to the driver"""
	try:
		# Optionally, you can add filters here like {"docstatus": 0} if you only want active ones
		vehicles = frappe.get_all("Vehicle", fields=["name", "license_plate", "make", "model"])

		ResponseHandler.success(vehicles)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_all_vehicles API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500, title=_("Server Error"), message="An unexpected error occurred."
		)


@frappe.whitelist()
def get_vehicle_details():
	"""Returns the full details of a specific vehicle"""
	try:
		params = get_request_params()
		vehicle_name = params.get("vehicle_name")

		if not vehicle_name:
			frappe.throw(_("Missing 'vehicle_name' parameter."), title=_("Missing Information"))

		if not frappe.db.exists("Vehicle", vehicle_name):
			frappe.throw(_("Vehicle {0} not found.").format(vehicle_name), title=_("Not Found"))

		vehicle = frappe.get_doc("Vehicle", vehicle_name)

		ResponseHandler.success(vehicle)
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_vehicle_details API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500, title=_("Server Error"), message="An unexpected error occurred."
		)


@frappe.whitelist()
def get_vpi_schema():
	"""Returns the form fields and options so the mobile app can build the VPI form dynamically"""
	try:
		meta = frappe.get_meta("Vehicle Pre-Inspection Check")
		fields = []

		for f in meta.fields:
			# Skip pure layout elements but keep data fields
			if f.fieldtype not in ("HTML", "Column Break"):
				options = f.options
				if f.fieldtype == "Select" and f.options:
					options = f.options.split("\n")

				fields.append(
					{
						"fieldname": f.fieldname,
						"label": f.label,
						"fieldtype": f.fieldtype,
						"options": options,
						"mandatory": f.reqd,
						"hidden": f.hidden,
					}
				)

		ResponseHandler.success(fields)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_vpi_schema API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500, title=_("Server Error"), message="An unexpected error occurred."
		)
