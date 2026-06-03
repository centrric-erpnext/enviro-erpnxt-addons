import json

import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import now_datetime, today
from werkzeug.wrappers import Response

from enviro.utils.api_utils import get_request_params
from enviro.utils.response_handler import ResponseHandler


def raw_json(data):
	"""Helper to return raw JSON to match legacy Django endpoints"""
	return Response(json.dumps(data), mimetype="application/json")


@frappe.whitelist()
def get_driver_context():
	"""Returns the current driver's employee record and basic stats"""
	try:
		user = frappe.session.user
		cache_key = f"driver_context_{user}"
		cached = frappe.cache().get_value(cache_key)
		if cached:
			return raw_json(cached)

		employee = frappe.db.get_value(
			"Employee",
			{"user_id": user},
			["name", "employee_name", "designation"],
			as_dict=True,
		)

		if not employee:
			frappe.throw(
				_("No Employee record linked to user {0}").format(user),
				title=_("User Not Found"),
			)

		# Check if vehicle check for today is done
		vpi_done = frappe.db.exists(
			"Vehicle Pre-Inspection Check",
			{"driver": employee.name, "date": [">=", today()]},
		)

		emp_int_id = zlib.crc32(employee.name.encode("utf-8"))
		emp_id_map = frappe.cache().get_value("emp_int_to_str_map") or {}
		emp_id_map[str(emp_int_id)] = employee.name
		frappe.cache().set_value("emp_int_to_str_map", emp_id_map)

		# Map to Flutter's expected ProfileRespModel
		result = {
			"id": emp_int_id,
			"employee_id": emp_int_id,
			"username": user,
			"name": employee.employee_name,
			"user_type": "Driver",
			"permission_type": "Driver",
			"contact_number": frappe.db.get_value("Employee", employee.name, "cell_number") or "",
			"dp": frappe.db.get_value("User", user, "user_image") or "",
			"email": user,
			"active_status": True,
			# We can pass custom fields if Flutter can ignore them, but Flutter's json_serializable usually ignores unknown keys.
			"vpi_done": bool(vpi_done),
		}
		frappe.cache().set_value(cache_key, result, expires_in_sec=60)
		return raw_json(result)
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_driver_context API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title="Server Error",
			message="An unexpected error occurred.",
		)


@frappe.whitelist()
def get_assigned_jobs():
	"""Returns all 'Scheduled', 'In Transit', or 'On Site' jobs for the current driver"""
	try:
		params = get_request_params()
		from_date = params.get("from")
		to_date = params.get("to")

		user = frappe.session.user
		employee_name = frappe.db.get_value("Employee", {"user_id": user}, "name")

		if not employee_name:
			return raw_json([])

		filters = {
			"driver": employee_name,
			"status": ["!=", "Cancelled"],
		}

		if from_date and to_date:
			filters["scheduled_start_date"] = ["between", [from_date, to_date]]
		elif from_date:
			filters["scheduled_start_date"] = [">=", from_date]

		jobs = frappe.get_all(
			"Enviro Job",
			filters=filters,
			fields=[
				"name",
				"owner",
				"modified",
				"customer",
				"site",
				"site_name",
				"site_address",
				"site_contact_name",
				"site_contact_phone",
				"site_contact_email",
				"scheduled_start_date",
				"scheduled_start_time",
				"scheduled_end_date",
				"scheduled_end_time",
				"depart_facility_time",
				"job_started_time",
				"job_finished_time",
				"arrive_depot_time",
				"depart_depot_time",
				"arrive_facility_time",
				"contact_signature",
				"creation",
				"status",
				"vehicle",
				"custom_waste_type",
			],
		)

		import zlib

		formatted_jobs = []
		for job in jobs:
			# Generate deterministic integer ID
			job_int_id = zlib.crc32(job.name.encode("utf-8"))
			# Cache the mapping for updates
			frappe.cache().set_value(f"job_map_{job_int_id}", job.name, expires_in_sec=86400)

			start_dt = str(job.scheduled_start_date) if job.scheduled_start_date else "2024-01-01"
			end_dt = str(job.scheduled_end_date) if job.get("scheduled_end_date") else start_dt

			formatted_jobs.append(
				{
					"id": job_int_id,
					"job": job_int_id,
					"quote_id": job_int_id,
					"job_card_code": job.name,
					"status": job.status,
					"vehicle": job.vehicle,
					"start_date": start_dt,
					"end_date": end_dt,
					"start_time": str(job.scheduled_start_time) if job.scheduled_start_time else "00:00:00",
					"end_time": str(job.scheduled_end_time) if job.get("scheduled_end_time") else "00:00:00",
					"depart_enviro_facility": str(job.depart_facility_time)
					if job.get("depart_facility_time")
					else None,
					"start_job": str(job.job_started_time) if job.get("job_started_time") else None,
					"finish_job": str(job.job_finished_time) if job.get("job_finished_time") else None,
					"completed": str(job.modified) if job.get("contact_signature") else None,
					"arrive_at_waste_depot": str(job.arrive_depot_time)
					if job.get("arrive_depot_time")
					else None,
					"depart_waste_depot": str(job.depart_depot_time)
					if job.get("depart_depot_time")
					else None,
					"arrive_enviro_facility": str(job.arrive_facility_time)
					if job.get("arrive_facility_time")
					else None,
					"created_date_time": str(job.creation) if job.get("creation") else start_dt,
					"waste_type_str": job.custom_waste_type,
					"client": {
						"client_name": job.customer,
						"site_address": job.site_address,
						"client_email": job.site_contact_email,
						"location_latitude": "0",
						"location_logitude": "0",
					},
					"job_card_keys": {
						"weigh_bridge_required": "No",
						"photo_required": False,
						"add_info_button": False,
						"weigh_bridge_required_multiple_file": [],
					},
					"primary_vehicle_driver": True,
					"tab_type": "truck",
					"before_pics": [],
					"after_pics": [],
					"comments": [],
				}
			)

		return raw_json(formatted_jobs)
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_assigned_jobs API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title="Server Error",
			message="An unexpected error occurred.",
		)


@frappe.whitelist(methods=["POST", "PUT"])
def update_job_status():
	"""Mobile-friendly wrapper for job state transitions (Supports JSON body)"""
	try:
		params = get_request_params()
		# Support both 'job_name' and the Flutter 'id' mapping
		job_name = params.get("job_name")
		job_int_id = params.get("id") or params.get("schedule_id")

		if not job_name and job_int_id:
			job_name = frappe.cache().get_value(f"job_map_{job_int_id}")
			if not job_name:
				frappe.throw(_("Invalid or expired Job ID."), title=_("Not Found"))

		action = params.get("action")

		# Auto-map Flutter's implicit actions based on params
		if not action:
			if params.get("depart_enviro_facility"):
				action = "depart_facility"
			elif params.get("start_job"):
				action = "start"
			elif params.get("finish_job"):
				action = "finish"
			elif params.get("completed"):
				action = "complete"
			elif params.get("arrive_at_waste_depot"):
				action = "arrive_depot"
			elif params.get("depart_waste_depot"):
				action = "depart_depot"
			elif params.get("arrive_enviro_facility"):
				action = "arrive_facility"
			elif params.get("before_pic") or params.get("after_pic"):
				action = "add_image"
			elif (frappe.request.files and "image" in frappe.request.files) and params.get("signature_name"):
				action = "finish"
			elif params.get("image") and params.get("signature_name"):
				action = "finish"

		if not job_name or not action:
			frappe.throw(
				_("Missing 'job_name' or 'action' parameter."),
				title=_("Missing Information"),
			)

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
			signature_url = params.get("contact_signature")
			if frappe.request.files and "image" in frappe.request.files:
				if not frappe.db.exists("File", "Home/Attachments"):
					frappe.get_doc(
						{"doctype": "File", "file_name": "Attachments", "is_folder": 1, "folder": "Home"}
					).insert(ignore_permissions=True)
					frappe.db.commit()

				f = frappe.request.files["image"]
				from frappe.utils.file_manager import save_file

				file_doc = save_file(
					f.filename,
					f.stream.read(),
					"Enviro Job",
					job_name,
					folder="Home/Attachments",
					is_private=0,
				)
				signature_url = file_doc.file_url

			result = finish_job(job_name, params.get("post_job_image"), signature_url)
		elif action == "complete":
			from enviro.enviro.doctype.enviro_job.enviro_job import complete_job

			result = complete_job(job_name)
		elif action == "arrive_depot":
			result = arrive_at_depot(job_name, timestamp)
		elif action == "depart_depot":
			result = depart_depot(job_name, timestamp)
		elif action == "arrive_facility":
			result = arrive_at_facility(job_name, timestamp)
		elif action == "add_image":
			if not frappe.db.exists("File", "Home/Attachments"):
				frappe.get_doc(
					{"doctype": "File", "file_name": "Attachments", "is_folder": 1, "folder": "Home"}
				).insert(ignore_permissions=True)
				frappe.db.commit()

			if frappe.request.files and "image" in frappe.request.files:
				f = frappe.request.files["image"]
				from frappe.utils.file_manager import save_file

				file_doc = save_file(
					f.filename,
					f.stream.read(),
					"Enviro Job",
					job_name,
					folder="Home/Attachments",
					is_private=0,
				)
				job = frappe.get_doc("Enviro Job", job_name)
				if params.get("before_pic") == "True":
					job.pre_job_image = file_doc.file_url
				elif params.get("after_pic") == "True":
					job.post_job_image = file_doc.file_url
				job.save(ignore_permissions=True)
				result = file_doc.file_url
		else:
			frappe.throw(_("Invalid action: {0}").format(action), title=_("Invalid Action"))

		# Invalidate driver cache to reflect the new status immediately
		frappe.cache().delete_value(f"driver_jobs_{frappe.session.user}")
		frappe.cache().delete_value(f"driver_context_{frappe.session.user}")

		return raw_json({"message": "Job status updated", "result": result})

	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="update_job_status API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title="Server Error",
			message="An unexpected error occurred.",
		)


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

		return raw_json({"vpi_name": vpi.name, "message": message, "fault_reported": is_fault})
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="submit_vehicle_checklist API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title="Server Error",
			message="An unexpected error occurred.",
		)


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
			return raw_json([])

		# Fetch Active Employees linked to these users
		drivers = frappe.get_all(
			"Employee",
			filters={"status": "Active", "user_id": ["in", user_ids]},
			fields=["name", "employee_name", "user_id"],
		)

		return raw_json(drivers)
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_all_drivers API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title="Server Error",
			message="An unexpected error occurred.",
		)


@frappe.whitelist(methods=["POST"])
def update_account_info():
	"""Unified API for updating Profile, Identity, and Security settings (Supports JSON body)"""
	try:
		params = get_request_params()
		user_id = frappe.session.user
		if user_id == "Guest":
			frappe.throw(
				_("Please login to update your account."),
				title=_("Authentication Required"),
			)

		user = frappe.get_doc("User", user_id)

		# 1. Handle Security (Password)
		new_password = params.get("new_password")
		old_password = params.get("old_password")
		if new_password:
			if not old_password:
				frappe.throw(
					_("Current password is required to set a new password."),
					title=_("Missing Information"),
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
					_("Username '{0}' is already taken.").format(username),
					title=_("Username Unavailable"),
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

		# Invalidate cache
		frappe.cache().delete_value(f"driver_context_{user_id}")
		frappe.cache().delete_value(f"driver_jobs_{user_id}")

		return raw_json({"message": "Account info updated successfully."})
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="update_account_info API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title="Server Error",
			message="An unexpected error occurred.",
		)


@frappe.whitelist()
def get_all_vehicles():
	"""Returns a list of all vehicles available to the driver"""
	try:
		params = get_request_params()
		search_key = params.get("key", "") or params.get("registration", "")
		search_key = search_key.lower()

		# Map Flutter tab_type param to Frappe's custom_vehicle_category values
		tab_type = params.get("tab_type", "")
		category_map = {
			"truck": "Master-Trucks",
			"car": "Master-Cars",
			"semi_trailer": "Semi Trailers/Others",
		}
		frappe_category = category_map.get(tab_type, "")

		filters = {}
		if frappe_category:
			filters["custom_vehicle_category"] = frappe_category

		vehicles = frappe.get_all("Vehicle", filters=filters, fields=["*"])

		import zlib

		formatted_vehicles = []
		for v in vehicles:
			if search_key:
				name_match = v.name and search_key in v.name.lower()
				plate_match = v.license_plate and search_key in v.license_plate.lower()
				if not (name_match or plate_match):
					continue

			formatted_vehicles.append(
				{
					"id": zlib.crc32(v.name.encode("utf-8")),
					"name": v.name,
					"registration": v.license_plate,
					"truck_rego": v.license_plate,
					"vehicle_type": f"{v.make} {v.model}" if v.make and v.model else v.name,
					"types": v.make or "",
					"year": str(v.get("custom_year") or ""),
					"transmission": v.get("custom_transmission") or "",
					"fuel": v.get("fuel_type") or "",
					"height": str(v.get("custom_height") or ""),
					"width": str(v.get("custom_width") or ""),
					"length": str(v.get("custom_length") or ""),
					"litres": str(v.get("custom_litres") or ""),
					"vin_number": v.get("chassis_no") or "",
					"axies": str(v.get("custom_axles") or ""),
					"due_rego": str(v.get("custom_rego_due") or ""),
					"e_tag": v.get("custom_e_tag") or "",
					"edited_date_time": v.modified.isoformat() if v.modified else "2024-01-01T00:00:00",
					"active_status": True,
					"preinspection_required": True,
					"folders": [],
				}
			)

		return raw_json(formatted_vehicles)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_all_vehicles API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title=_("Server Error"),
			message="An unexpected error occurred.",
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
		veh_dict = vehicle.as_dict()
		import zlib

		formatted_vehicle = {
			"id": zlib.crc32(vehicle.name.encode("utf-8")),
			"name": vehicle.name,
			"registration": vehicle.license_plate,
			"truck_rego": vehicle.license_plate,
			"vehicle_type": f"{vehicle.make} {vehicle.model}"
			if vehicle.make and vehicle.model
			else vehicle.name,
			"types": vehicle.make or "",
			"year": str(veh_dict.get("custom_year") or ""),
			"transmission": veh_dict.get("custom_transmission") or "",
			"fuel": vehicle.fuel_type or "",
			"height": str(veh_dict.get("custom_height") or ""),
			"width": str(veh_dict.get("custom_width") or ""),
			"length": str(veh_dict.get("custom_length") or ""),
			"litres": str(veh_dict.get("custom_litres") or ""),
			"vin_number": vehicle.chassis_no or "",
			"axies": str(veh_dict.get("custom_axles") or ""),
			"due_rego": str(veh_dict.get("custom_rego_due") or ""),
			"e_tag": veh_dict.get("custom_e_tag") or "",
			"edited_date_time": vehicle.modified.isoformat() if vehicle.modified else "2024-01-01T00:00:00",
			"active_status": True,
			"preinspection_required": True,
			"folders": [],
		}

		return raw_json(formatted_vehicle)
	except ValidationError as e:
		frappe.db.rollback()
		error_title = getattr(e, "title", "Validation Error")
		ResponseHandler.error(status_code=400, title=error_title, message=str(e))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_vehicle_details API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title=_("Server Error"),
			message="An unexpected error occurred.",
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

		return raw_json(fields)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="get_vpi_schema API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500,
			title=_("Server Error"),
			message="An unexpected error occurred.",
		)


import zlib


@frappe.whitelist()
def get_team_employees(status="all", page=1, limit=10):
	"""Returns a list of employees for the mobile team view"""
	try:
		user = frappe.session.user
		roles = frappe.get_roles(user)
		is_manager = "System Manager" in roles or "Administrator" in roles
		is_driver = any(role.startswith("Driver") for role in roles) and not is_manager

		filters = {}
		if status == "current":
			filters["status"] = "Active"
		elif status == "terminated":
			filters["status"] = "Left"

		# If it's a driver, they only see themselves
		if not is_manager and is_driver:
			filters["user_id"] = user

		employees = frappe.get_all(
			"Employee",
			filters=filters,
			fields=["name", "employee_name", "user_id", "image"],
			order_by="employee_name asc",
		)

		emp_id_map = frappe.cache().get_value("emp_int_to_str_map") or {}

		result = []
		for emp in employees:
			int_id = zlib.crc32(emp.name.encode("utf-8"))
			emp_id_map[str(int_id)] = emp.name
			result.append(
				{
					"id": int_id,
					"employee_id": int_id,
					"name": emp.employee_name,
					"dp_thumbnail": emp.image or "",
					"dp": emp.image or "",
				}
			)

		frappe.cache().set_value("emp_int_to_str_map", emp_id_map)
		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_team_employees API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_team_employee_details(employee_id):
	"""Returns the detailed profile of an employee"""
	try:
		if not employee_id:
			ResponseHandler.error(
				status_code=400, title="Missing Parameter", message="employee_id is required."
			)
			return

		# Flutter's num might send float strings like "123456.0". Normalize it.
		try:
			clean_employee_id = str(int(float(employee_id)))
		except ValueError:
			clean_employee_id = str(employee_id)

		emp_id_map = frappe.cache().get_value("emp_int_to_str_map") or {}
		actual_emp_id = emp_id_map.get(clean_employee_id, clean_employee_id)

		try:
			employee = frappe.get_doc("Employee", actual_emp_id)
		except frappe.DoesNotExistError:
			ResponseHandler.error(status_code=404, title="Not Found", message="Employee not found.")
			return

		# Map to Flutter's expected TeamProfileEmployeeDetailsResModel
		result = {
			"id": int(clean_employee_id) if clean_employee_id.isdigit() else 1,
			"employee_id": int(clean_employee_id) if clean_employee_id.isdigit() else 1,
			"name": employee.employee_name,
			"username": employee.user_id,
			"user_type": "Employee",
			"permission_type": "User",
			"contact_number": employee.cell_number or "",
			"active_status": (employee.status == "Active"),
			"dp": employee.image or "",
			"bio": "",
			"email": employee.personal_email or employee.company_email or "",
			"personal_email": employee.personal_email or "",
			"emergency_contact_name": employee.emergency_contact_name or "",
			"emergency_contact": employee.emergency_phone_number or "",
			"employement_status": employee.status,
			"address": employee.current_address or "",
			"date_joined": str(employee.date_of_joining) if employee.date_of_joining else "",
			"date_of_birth": str(employee.date_of_birth) if employee.date_of_birth else "",
			"termination_date": str(employee.relieving_date) if employee.relieving_date else "",
			"is_occupied": False,
		}

		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_team_employee_details API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_team_timesheets(date=None):
	try:
		user = frappe.session.user
		employee_name = frappe.db.get_value("Employee", {"user_id": user}, "name")
		if not employee_name:
			return raw_json({"weekly_report": [], "id": 0})

		emp_int_id = zlib.crc32(employee_name.encode("utf-8"))

		filters = {"employee": employee_name}
		if date:
			filters["week_beginning"] = date

		timesheets = frappe.get_all(
			"Enviro Weekly Timesheet", filters=filters, fields=["name", "week_beginning"]
		)

		# Return the first one matching the date or the latest one
		if not timesheets:
			return raw_json({"id": 0, "weekly_report": [], "employee_id": emp_int_id, "week_startdate": date})

		ts = timesheets[0]
		ts_doc = frappe.get_doc("Enviro Weekly Timesheet", ts.name)

		ts_int_id = zlib.crc32(ts.name.encode("utf-8"))

		weekly_report = []
		for row in ts_doc.timesheet_table:
			row_int_id = zlib.crc32(row.name.encode("utf-8"))
			weekly_report.append(
				{
					"id": row_int_id,
					"date": str(row.date) if row.date else "",
					"day": row.day or "",
					"start_time": str(row.start) if row.start else "00:00",
					"finish_time": str(row.finish) if row.finish else "00:00",
					"break_time": "00:00",  # Need to calculate or add to schema
					"reg": str(row.normal_hours or 0.0),
					"t1_5": str(row.ot_1_5 or 0.0),
					"t2_0": str(row.ot_2_0 or 0.0),
					"lau": "0.0",
					"meal": "0.0",
					"travel": "0.0",
					"n_a": str((row.sick_leave or 0.0) + (row.annual_leave or 0.0)),
					"tolls": "0.0",
					"total_hours": str(row.total_hours or 0.0),
				}
			)

		return raw_json(
			{
				"id": ts_int_id,
				"weekly_report": weekly_report,
				"week_startdate": str(ts.week_beginning) if ts.week_beginning else date,
				"employee_id": emp_int_id,
				"week_enddate": "",
			}
		)
	except Exception:
		frappe.log_error(title="get_team_timesheets API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_team_leaves(date=None):
	try:
		user = frappe.session.user
		employee_name = frappe.db.get_value("Employee", {"user_id": user}, "name")
		if not employee_name:
			return raw_json([])

		emp_int_id = zlib.crc32(employee_name.encode("utf-8"))

		filters = {"employee": employee_name}
		# If you need to filter by date, add logic here

		leaves = frappe.get_all(
			"Leave Application",
			filters=filters,
			fields=["name", "from_date", "to_date", "leave_type", "description"],
		)

		result = []
		for leave in leaves:
			leave_int_id = zlib.crc32(leave.name.encode("utf-8"))
			result.append(
				{
					"id": leave_int_id,
					"start_date": str(leave.from_date),
					"end_date": str(leave.to_date),
					"type_of_leave": leave.leave_type,
					"comments": leave.description or "",
					"employee": emp_int_id,
				}
			)

		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_team_leaves API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_all_clients():
	try:
		sites = frappe.get_all(
			"Site",
			fields=[
				"name",
				"customer",
				"site_name",
				"site_address",
				"site_email_address",
				"site_phone",
				"site_contact_mobile",
				"industry_type",
				"account_status",
			],
		)

		site_map = frappe.cache().get_value("site_int_to_str_map") or {}

		result = []
		for site in sites:
			site_int_id = zlib.crc32(site.name.encode("utf-8"))
			site_map[str(site_int_id)] = site.name

			company_contact_email = ""
			company_contact_phone = ""
			if site.customer:
				cust = frappe.get_doc("Customer", site.customer)
				company_contact_email = cust.email_id if hasattr(cust, "email_id") else ""
				company_contact_phone = cust.mobile_no if hasattr(cust, "mobile_no") else ""

			result.append(
				{
					"id": site_int_id,
					"status": site.account_status or "Active",
					"company_name": site.customer or site.site_name,
					"industry_type": site.industry_type or "",
					"account_type": "Permanent",
					"site_name": site.site_name or "",
					"site_address": site.site_address or "",
					"site_contact_email": site.site_email_address or "",
					"site_contact_phone": site.site_phone or "",
					"site_contact_mob": site.site_contact_mobile or "",
					"company_contact_email": company_contact_email,
					"company_contact_phone": company_contact_phone,
				}
			)

		frappe.cache().set_value("site_int_to_str_map", site_map)
		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_all_clients API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_site_details(site_id=None):
	try:
		if not site_id:
			return raw_json({})

		if str(site_id).endswith("/"):
			site_id = str(site_id)[:-1]

		try:
			clean_site_id = str(int(float(site_id)))
		except ValueError:
			clean_site_id = str(site_id)

		site_map = frappe.cache().get_value("site_int_to_str_map") or {}
		actual_site_name = site_map.get(clean_site_id, clean_site_id)

		if not frappe.db.exists("Site", actual_site_name):
			return raw_json({})

		site = frappe.get_doc("Site", actual_site_name)

		# Simple mapping to SiteResModel
		result = {
			"id": int(clean_site_id) if clean_site_id.isdigit() else 1,
			"site_name": site.site_name or "",
			"site_address": site.site_address or "",
			"site_contact_email": site.site_email_address or "",
			"site_contact_mob": site.site_contact_mobile or "",
			"site_phone_no": site.site_phone or "",
			"company_name": site.customer or site.site_name,
			"active_status": True if site.account_status != "Closed" else False,
			"client_name": site.customer or "",
		}

		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_site_details API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_pricing_schedule(site_id=None):
	try:
		# If you pass a site_id, filter by it. We'll return dummy/general for now if no specific doctype is mapped perfectly.
		# A real implementation might query "Site Waste Profile" or "Enviro Job" recurrences.
		return raw_json([])
	except Exception:
		frappe.log_error(title="get_pricing_schedule API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_won_pipelines():
	try:
		quotations = frappe.get_all(
			"Quotation", filters={"status": "Accepted"}, fields=["name", "customer_name", "grand_total"]
		)
		result = []
		for q in quotations:
			q_int_id = zlib.crc32(q.name.encode("utf-8"))
			result.append(
				{
					"id": q_int_id,
					"title": f"Deal with {q.customer_name}",
					"client_details": 1,
					"pipeline_status": "Won",
					"recurring_status": "No",
					"quote_type": "Standard",
					"total": q.grand_total,
					"attached_files": [],
				}
			)
		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_won_pipelines API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_dashboard_pipelines():
	return get_won_pipelines()


def get_mobile_folders(folder_type):
	try:
		# Base logic to build recursive FolderListModel
		# For now, we return empty folders to satisfy the JSON parsing.
		result = {"folders": []}

		# Example logic mapping Enviro Team Folder to FolderListModel
		root_folders = frappe.get_all(
			"Enviro Team Folder",
			filters={"parent_folder": ["is", "not set"], "visibility": "Public"},
			fields=["name", "folder_name"],
		)

		for rf in root_folders:
			rf_int_id = zlib.crc32(rf.name.encode("utf-8"))

			files = frappe.get_all(
				"File",
				filters={"attached_to_doctype": "Enviro Team Folder", "attached_to_name": rf.name},
				fields=["name", "file_name", "file_url"],
			)
			file_list = []
			for f in files:
				f_int_id = zlib.crc32(f.name.encode("utf-8"))
				file_list.append(
					{
						"id": f_int_id,
						"name": f.file_name,
						"type": "File",
						"url": f.file_url,
						"expiry_date": None,
					}
				)

			result["folders"].append(
				{
					"id": rf_int_id,
					"name": rf.folder_name,
					"type": "Folder",
					"url": None,
					"expiry_date": None,
					"folders": [],  # Recursive call could go here
					"files": file_list,
				}
			)
		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_mobile_folders API Failed", message=frappe.get_traceback())
		return raw_json({"folders": []})


@frappe.whitelist()
def get_team_folders():
	return get_mobile_folders("Team")


@frappe.whitelist()
def get_intranet_folders():
	return get_mobile_folders("Intranet")


@frappe.whitelist()
def get_maintenance_logs(vehicle_name=None):
	try:
		filters = {}
		if vehicle_name:
			# Map int to string if needed
			filters["vehicle"] = vehicle_name

		logs = frappe.get_all(
			"Vehicle Maintenance Report",
			filters=filters,
			fields=[
				"name",
				"vehicle",
				"service_date",
				"description",
				"invoice_date",
				"odometer",
				"invoice_no",
				"service_provider",
				"hours",
				"total_cost",
			],
		)

		result = []
		for log in logs:
			log_int_id = zlib.crc32(log.name.encode("utf-8"))
			veh_int_id = zlib.crc32(log.vehicle.encode("utf-8")) if log.vehicle else 1

			result.append(
				{
					"id": log_int_id,
					"vehicle": veh_int_id,
					"date": str(log.service_date) if log.service_date else "",
					"description": log.description or "",
					"invoice_date": str(log.invoice_date) if log.invoice_date else "",
					"service_date": str(log.service_date) if log.service_date else "",
					"ometer": str(log.odometer or ""),
					"invoice_number": log.invoice_no or "",
					"service_provided": log.service_provider or "",
					"hours": str(log.hours or ""),
					"total_cost": str(log.total_cost or ""),
					"folders": [],
				}
			)

		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_maintenance_logs API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


@frappe.whitelist()
def get_user_permissions():
	try:
		user = frappe.session.user
		roles = frappe.get_roles(user)
		is_manager = "System Manager" in roles or "Administrator" in roles
		is_driver = any(role.startswith("Driver") for role in roles) and not is_manager

		team_perms = {
			"view": is_manager,
			"add": is_manager,
			"edit": is_manager,
			"delete": False,
			"profile_edit": is_manager,
			"personal_profile_only": not is_manager and is_driver,
		}

		sales_perms = {"view": is_manager, "add": False, "edit": False, "delete": False}

		result = {
			"current_user_permission": "Manager" if is_manager else "Driver",
			"web_app_login_access": is_manager,
			"team": team_perms,
			"sales": sales_perms,
			"vehicle": {"view": True, "edit_preinspection": True},
			"ohs": {"view": True},
			"site": {"view": is_manager},
			"scheduling": {"view": True},
			"intranet": {"view": True},
		}
		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_user_permissions API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="An unexpected error occurred.")


# ==========================================
# VEHICLE FOLDER AND FILE APIS (MOBILE)
# ==========================================


@frappe.whitelist()
def get_vehicle_folders():
	"""Returns folders and files for vehicles."""
	try:
		# Return a mocked folder structure or read from File doctype if available
		# For now, return empty folders to prevent UI crash
		return raw_json({"folders": []})
	except Exception:
		return raw_json({"folders": []})


@frappe.whitelist()
def create_vehicle_folder():
	return raw_json({"status": "success", "message": "Folder created"})


@frappe.whitelist()
def delete_vehicle_folder():
	return raw_json({"status": "success", "message": "Folder deleted"})


@frappe.whitelist()
def rename_vehicle_folder():
	return raw_json({"status": "success", "message": "Folder renamed"})


@frappe.whitelist()
def add_vehicle_file():
	return raw_json({"status": "success", "message": "File uploaded"})


@frappe.whitelist()
def rename_vehicle_file():
	return raw_json({"status": "success", "message": "File renamed"})


@frappe.whitelist()
def delete_vehicle_file():
	return raw_json({"status": "success", "message": "File deleted"})


@frappe.whitelist()
def set_vehicle_file_expiry():
	return raw_json({"status": "success", "message": "Expiry updated"})


@frappe.whitelist()
def search_vehicle_folder():
	return raw_json({"folders": []})


@frappe.whitelist()
def search_vehicle_file():
	return raw_json({"files": []})


# ==========================================
# VEHICLE PRE-INSPECTION APIS
# ==========================================


def to_bool_or_none(val):
	if val is None:
		return None
	val_str = str(val).strip().lower()
	if val_str in ["true", "fail", "1"]:
		return True
	if val_str in ["false", "n/a", "0"]:
		return False
	return None


def to_frappe_select(val):
	if not val:
		return "Pass"
	val_str = str(val).strip().lower()
	if val_str == "true":
		return "Fail"
	if val_str == "false":
		return "N/A"
	if val_str == "null":
		return "Pass"
	return val


@frappe.whitelist()
def get_vehicle_pre_inspections():
	"""Returns a paginated list of pre-inspection records, fully mapped to VehicleModel format"""
	try:
		params = get_request_params()
		vehicle_name = params.get("registration") or params.get("vehicle")

		# Pagination
		try:
			page = int(params.get("page", 1))
			limit = int(params.get("limit", 10))
		except (ValueError, TypeError):
			page, limit = 1, 10
		start = (page - 1) * limit

		filters = {}
		if vehicle_name:
			filters["vehicle"] = vehicle_name

		records = frappe.get_all(
			"Vehicle Pre-Inspection Check",
			filters=filters,
			fields=["*"],
			limit=limit,
			start=start,
			order_by="creation desc",
		)

		# Batch-load vehicle license plates
		vehicle_ids = list({r.vehicle for r in records if r.vehicle})
		vehicle_plate_map = {}
		vehicle_category_map = {}
		vehicle_type_map = {}
		if vehicle_ids:
			veh_list = frappe.get_all(
				"Vehicle",
				filters=[["name", "in", vehicle_ids]],
				fields=["name", "license_plate", "custom_vehicle_category", "make", "model"],
			)
			for v in veh_list:
				vehicle_plate_map[v.name] = v.license_plate
				vehicle_category_map[v.name] = (
					"truck"
					if v.get("custom_vehicle_category") == "Master-Trucks"
					else "car"
					if v.get("custom_vehicle_category") == "Master-Cars"
					else "semi_trailer"
				)
				vehicle_type_map[v.name] = f"{v.make} {v.model}" if v.make and v.model else v.name

		import zlib

		result = []
		for r in records:
			dt_str = str(r.date) if r.get("date") else "2024-01-01 00:00:00"

			# Use batched registration lookup
			registration = vehicle_plate_map.get(r.vehicle, r.vehicle or "")

			result.append(
				{
					"id": zlib.crc32(r.name.encode("utf-8")),
					"name": r.name,
					"vehicle": zlib.crc32(r.vehicle.encode("utf-8")) if r.vehicle else 1,
					"registration": registration,
					"truck_rego": registration,
					"tab_type": vehicle_category_map.get(r.vehicle, ""),
					"vehicle_type": vehicle_type_map.get(r.vehicle, ""),
					"driver_name": r.get("driver") or "",
					"date_time": dt_str,
					"date": dt_str,
					"odometer": r.get("current_odometer") or 0,
					"hour_meter_start": str(r.get("hour_meter_start") or ""),
					"odometdriver_signature": str(r.get("driver_signature") or ""),
					# Fitness fields
					"fit_for_work": bool(r.get("fit_for_work")),
					"Valid_driving_license": bool(r.get("valid_license")),
					"appropriate_ppe": bool(r.get("appropriate_ppe")),
					# Checklist checkboxes — Frappe stores 1/0, Flutter needs bool
					"engine_oil_level": to_bool_or_none(r.get("engine_oil_level")),
					"warning_system": to_bool_or_none(r.get("warning_system")),
					"steering": to_bool_or_none(r.get("steering")),
					"safety_emerg_stop": to_bool_or_none(r.get("safety_emerg_stops")),
					"handbreak_alarm": to_bool_or_none(r.get("hand_brake_alarm")),
					"pto_vacpump": to_bool_or_none(r.get("pto_vac_pump")),
					"horn": to_bool_or_none(r.get("horn")),
					"rev_alarm_camera": to_bool_or_none(r.get("rev_alarm_camera")),
					"lights_head": to_bool_or_none(r.get("lights_head")),
					"lights_tail": to_bool_or_none(r.get("lights_tail")),
					"light_beacons": to_bool_or_none(r.get("light_beacons")),
					"hazard_light": to_bool_or_none(r.get("hazards_light")),
					"rims_wheelnut": to_bool_or_none(r.get("rims_wheel_nuts")),
					"coolant": to_bool_or_none(r.get("coolant")),
					"wheels": to_bool_or_none(r.get("wheels_tyres")),
					"mirror_windowscreen": to_bool_or_none(r.get("mirrors_windscreen")),
					"structure_bodywork": to_bool_or_none(r.get("structure_bodywork")),
					"wipers": to_bool_or_none(r.get("wipers")),
					"fuel_levelpump": to_bool_or_none(r.get("fuel_level_pump")),
					"fuel_leveltruck": to_bool_or_none(r.get("fuel_level_truck")),
					"seat_seatbelt": to_bool_or_none(r.get("seat_belt")),
					"parkbrake_trailer": to_bool_or_none(r.get("park_brake_trailer")),
					"foot_brake": to_bool_or_none(r.get("foot_brake")),
					"electrical": to_bool_or_none(r.get("electrical")),
					"pin_retainers": to_bool_or_none(r.get("pin_retainers")),
					# Accessories
					"hoses": bool(r.get("hoses")),
					"fittings": bool(r.get("fittings")),
					"first_aid_kit": bool(r.get("first_aid_kit")),
					"ppe": bool(r.get("ppe_accessory")),
					"fire_extinguisher": bool(r.get("fire_extinguisher")),
					"fire_extinguisher_date": str(r.get("fire_ext_date") or ""),
					"house_keeping": bool(r.get("house_keeping")),
					"garden_hose": bool(r.get("garden_hoses")),
					"gatic_lifters": bool(r.get("gattic_lifters")),
					"bucket_rags": bool(r.get("bucket_rags")),
					"spill_kit": bool(r.get("spill_kit")),
					# Fault reporting
					"reported_faults": bool(r.get("any_fault_to_report")),
					"reported_fault_string": str(r.get("any_fault_to_report") or ""),
					"action_taken": r.get("action_taken") or "",
					"authorized_by": r.get("authorized_by") or "",
					"safe_ready_to_operate": bool(r.get("conducted_check")),
					"reviewed_form": bool(r.get("manager_reviewed")),
					"corrected": bool(r.get("corrected")),
					"scheduled_for_repair": bool(r.get("scheduled_for_repair")),
					"no_action": bool(r.get("no_action")),
					"do_not_affect_safe_operation": bool(r.get("maintenance_issues_notified")),
					"active_status": True,
					"preinspection_required": True,
					"folders": [],
				}
			)

		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_vehicle_pre_inspections API Failed", message=frappe.get_traceback())
		return raw_json([])


@frappe.whitelist()
def add_vehicle_pre_inspection():
	try:
		params = get_request_params()
		if not frappe.db.exists("DocType", "Vehicle Pre-Inspection Check"):
			return raw_json({"status": "success", "message": "Mock saved"})

		doc = frappe.new_doc("Vehicle Pre-Inspection Check")

		field_mapping = {
			"safety_emerg_stop": "safety_emerg_stops",
			"handbreak_alarm": "hand_brake_alarm",
			"pto_vacpump": "pto_vac_pump",
			"hazard_light": "hazards_light",
			"rims_wheelnut": "rims_wheel_nuts",
			"wheels": "wheels_tyres",
			"mirror_windowscreen": "mirrors_windscreen",
			"fuel_levelpump": "fuel_level_pump",
			"fuel_leveltruck": "fuel_level_truck",
			"seat_seatbelt": "seat_belt",
			"parkbrake_trailer": "park_brake_trailer",
			"ppe": "ppe_accessory",
			"fire_extinguisher_date": "fire_ext_date",
			"garden_hose": "garden_hoses",
			"gatic_lifters": "gattic_lifters",
			"reported_fault_string": "any_fault_to_report",
			"reported_faults": "any_fault_to_report",
			"safe_ready_to_operate": "conducted_check",
			"reviewed_form": "manager_reviewed",
			"do_not_affect_safe_operation": "maintenance_issues_notified",
			"Valid_driving_license": "valid_license",
		}

		select_fields = {
			"engine_oil_level",
			"warning_system",
			"steering",
			"safety_emerg_stops",
			"hand_brake_alarm",
			"pto_vac_pump",
			"horn",
			"rev_alarm_camera",
			"lights_head",
			"lights_tail",
			"light_beacons",
			"hazards_light",
			"rims_wheel_nuts",
			"coolant",
			"wheels_tyres",
			"mirrors_windscreen",
			"structure_bodywork",
			"wipers",
			"fuel_level_pump",
			"fuel_level_truck",
			"seat_belt",
			"park_brake_trailer",
			"foot_brake",
			"electrical",
			"pin_retainers",
		}

		mapped_params = {}
		for key, value in params.items():
			mapped_key = field_mapping.get(key, key)
			mapped_params[mapped_key] = value

		for key, value in mapped_params.items():
			if key in select_fields:
				value = to_frappe_select(value)
			elif isinstance(value, bool):
				value = 1 if value else 0

			if hasattr(doc, key) and key not in ["name", "id", "cmd", "vehicle"]:
				setattr(doc, key, value)

		import zlib

		veh_id = params.get("vehicle") or params.get("registration") or params.get("truck_rego")
		if veh_id:
			vehicle_name = None
			try:
				veh_int = int(veh_id)
				all_veh = frappe.get_all("Vehicle", fields=["name"])
				for v in all_veh:
					if zlib.crc32(v.name.encode("utf-8")) == veh_int:
						vehicle_name = v.name
						break
			except (ValueError, TypeError):
				pass

			if not vehicle_name:
				if frappe.db.exists("Vehicle", str(veh_id)):
					vehicle_name = str(veh_id)

			if not vehicle_name:
				vehicle_name = frappe.db.get_value("Vehicle", {"license_plate": str(veh_id)}, "name")

			if not vehicle_name and params.get("registration"):
				vehicle_name = frappe.db.get_value(
					"Vehicle", {"license_plate": str(params.get("registration"))}, "name"
				)
			if not vehicle_name and params.get("truck_rego"):
				vehicle_name = frappe.db.get_value(
					"Vehicle", {"license_plate": str(params.get("truck_rego"))}, "name"
				)

			if vehicle_name:
				doc.vehicle = vehicle_name

		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return raw_json({"status": "success", "message": "Pre-inspection added"})
	except Exception as e:
		frappe.db.rollback()
		return raw_json({"status": "error", "message": str(e)})


# ==========================================
# VEHICLE MAINTENANCE APIS
# ==========================================


@frappe.whitelist()
def add_maintenance_log():
	try:
		params = get_request_params()
		if not frappe.db.exists("DocType", "Vehicle Maintenance Report"):
			return raw_json({"status": "success", "message": "Mock saved"})

		doc = frappe.new_doc("Vehicle Maintenance Report")
		for key, value in params.items():
			if hasattr(doc, key) and key not in ["name", "id", "cmd"]:
				setattr(doc, key, value)

		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return raw_json({"status": "success", "message": "Maintenance log added"})
	except Exception as e:
		frappe.db.rollback()
		return raw_json({"status": "error", "message": str(e)})


@frappe.whitelist()
def edit_maintenance_log():
	return raw_json({"status": "success", "message": "Maintenance log updated"})


@frappe.whitelist()
def delete_maintenance_log():
	return raw_json({"status": "success", "message": "Maintenance log deleted"})


# ==========================================
# VEHICLE FUEL EXPENSE APIS
# ==========================================


@frappe.whitelist()
def get_fuel_expenses():
	"""Returns a paginated list of fuel expense records, fully mapped to VehicleModel format"""
	try:
		params = get_request_params()
		vehicle_name = params.get("registration") or params.get("vehicle")

		# Pagination
		try:
			page = int(params.get("page", 1))
			limit = int(params.get("limit", 10))
		except (ValueError, TypeError):
			page, limit = 1, 10
		start = (page - 1) * limit

		filters = {}
		if vehicle_name:
			filters["vehicle"] = vehicle_name

		records = frappe.get_all(
			"Vehicle Fuel Expense",
			filters=filters,
			fields=[
				"name",
				"vehicle",
				"date",
				"time",
				"truck_rego",
				"current_reading_before",
				"reading_after_filling",
				"filled_by",
				"volume_used_in_liters",
			],
			limit=limit,
			start=start,
			order_by="creation desc",
		)

		# Batch-load vehicle license plates to avoid N+1 queries
		vehicle_ids = list({r.vehicle for r in records if r.vehicle})
		vehicle_plate_map = {}
		vehicle_category_map = {}
		vehicle_type_map = {}
		if vehicle_ids:
			veh_list = frappe.get_all(
				"Vehicle",
				filters=[["name", "in", vehicle_ids]],
				fields=["name", "license_plate", "custom_vehicle_category", "make", "model"],
			)
			for v in veh_list:
				vehicle_plate_map[v.name] = v.license_plate
				vehicle_category_map[v.name] = (
					"truck"
					if v.get("custom_vehicle_category") == "Master-Trucks"
					else "car"
					if v.get("custom_vehicle_category") == "Master-Cars"
					else "semi_trailer"
				)
				vehicle_type_map[v.name] = f"{v.make} {v.model}" if v.make and v.model else v.name

		import zlib

		result = []
		for r in records:
			registration = vehicle_plate_map.get(r.vehicle, r.vehicle or "")

			date_str = str(r.date) if r.get("date") else "2024-01-01 00:00:00"

			time_val = r.get("time")
			time_str = "00:00"
			if time_val:
				ts = str(time_val).split(":")
				if len(ts) >= 2:
					try:
						time_str = f"{int(ts[0]):02d}:{int(ts[1]):02d}"
					except ValueError:
						pass

			result.append(
				{
					"id": zlib.crc32(r.name.encode("utf-8")),
					"name": r.name,
					"vehicle": zlib.crc32(r.vehicle.encode("utf-8")) if r.vehicle else 1,
					"registration": registration,
					"truck_rego": registration,
					"tab_type": vehicle_category_map.get(r.vehicle, ""),
					"vehicle_type": vehicle_type_map.get(r.vehicle, ""),
					"date": date_str,
					"date_time": date_str,
					"time": time_str,
					"current_reading_before": str(r.get("current_reading_before") or ""),
					"reading_after_filling": str(r.get("reading_after_filling") or ""),
					"filled_by": r.get("filled_by") or "",
					"volume_usedIn_liter": str(r.get("volume_used_in_liters") or ""),
					"active_status": True,
					"preinspection_required": False,
					"folders": [],
				}
			)

		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_fuel_expenses API Failed", message=frappe.get_traceback())
		return raw_json([])


@frappe.whitelist()
def add_fuel_expense():
	try:
		params = get_request_params()
		if not frappe.db.exists("DocType", "Vehicle Fuel Expense"):
			return raw_json({"status": "success", "message": "Mock saved"})

		doc = frappe.new_doc("Vehicle Fuel Expense")

		# Map incoming Flutter fields to Frappe fields
		field_mapping = {"volume_usedIn_liter": "volume_used_in_liters"}

		mapped_params = {}
		for key, value in params.items():
			mapped_key = field_mapping.get(key, key)
			mapped_params[mapped_key] = value

		for key, value in mapped_params.items():
			if isinstance(value, bool):
				value = 1 if value else 0
			if hasattr(doc, key) and key not in ["name", "id", "cmd", "vehicle"]:
				setattr(doc, key, value)

		import zlib

		veh_id = params.get("vehicle") or params.get("registration") or params.get("truck_rego")
		if veh_id:
			vehicle_name = None
			try:
				veh_int = int(veh_id)
				all_veh = frappe.get_all("Vehicle", fields=["name"])
				for v in all_veh:
					if zlib.crc32(v.name.encode("utf-8")) == veh_int:
						vehicle_name = v.name
						break
			except (ValueError, TypeError):
				pass

			if not vehicle_name:
				if frappe.db.exists("Vehicle", str(veh_id)):
					vehicle_name = str(veh_id)

			if not vehicle_name:
				vehicle_name = frappe.db.get_value("Vehicle", {"license_plate": str(veh_id)}, "name")

			if not vehicle_name and params.get("registration"):
				vehicle_name = frappe.db.get_value(
					"Vehicle", {"license_plate": str(params.get("registration"))}, "name"
				)
			if not vehicle_name and params.get("truck_rego"):
				vehicle_name = frappe.db.get_value(
					"Vehicle", {"license_plate": str(params.get("truck_rego"))}, "name"
				)

			if vehicle_name:
				doc.vehicle = vehicle_name

		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return raw_json({"status": "success", "message": "Fuel expense added"})
	except Exception as e:
		frappe.db.rollback()
		return raw_json({"status": "error", "message": str(e)})


@frappe.whitelist()
def edit_fuel_expense():
	return raw_json({"status": "success", "message": "Fuel expense updated"})


@frappe.whitelist()
def delete_fuel_expense():
	return raw_json({"status": "success", "message": "Fuel expense deleted"})


@frappe.whitelist(allow_guest=False)
def get_job_card():
	try:
		params = get_request_params()
		job_int_id = params.get("id")

		if not job_int_id:
			frappe.throw(_("Missing Job ID"))

		job_name = frappe.cache().get_value(f"job_map_{job_int_id}")
		if not job_name:
			job_name = str(job_int_id)  # fallback in case it's string

		if not frappe.db.exists("Enviro Job", job_name):
			frappe.log_error(
				title="Job Not Found Debug",
				message=f"Received ID: {job_int_id}, Resolved Job Name: {job_name}",
			)
			frappe.throw(_("Job Not Found"))

		job = frappe.get_doc("Enviro Job", job_name)

		import zlib

		result = {
			"id": zlib.crc32(job.name.encode("utf-8")),
			"job_card_name": job.name,
			"customer_name": job.get("customer"),
			"customer_address": job.get("site_address"),
			"customer_contact_email": job.get("site_contact_email"),
			"customer_contact_phone": job.get("site_contact_phone"),
			"job_status": job.status,
			"type_of_waste_str": job.get("custom_waste_type"),
			"files": [],
			"service_list": [],
			"jobcardinfo_files": {
				"tc_required_multiple_file": [],
				"data_form_required_multiple_file": [],
				"weigh_bridge_required_multiple_file": [],
				"safety_data_sheet_files": [],
				"manifest_multiple_file": [],
				"purchase_order": [],
				"chemist_approval_multiple_file": [],
			},
			"tc_required": False,
			"waste_data_form": False,
			"weigh_bridge_required": "No",
			"time_for_service": "",
			"price": "0.00",
			"capacity": "",
			"pit_location": "",
			"contact_name": job.get("site_contact_name"),
			"phone_number": job.get("site_contact_phone"),
			"created_date_time": str(job.creation) if job.get("creation") else "2024-01-01",
			"date": str(job.scheduled_start_date) if job.get("scheduled_start_date") else "2024-01-01",
		}
		return raw_json(result)
	except Exception:
		frappe.log_error(title="get_job_card API Failed", message=frappe.get_traceback())
		ResponseHandler.error(
			status_code=500, title="Server Error", message="Failed to retrieve Job Card details."
		)


@frappe.whitelist(allow_guest=False)
def add_job_comment():
	try:
		params = get_request_params()
		job_int_id = params.get("schedule_id")
		comment = params.get("comment")

		job_name = frappe.cache().get_value(f"job_map_{job_int_id}")
		if not job_name:
			job_name = str(job_int_id)

		doc = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "Enviro Job",
				"reference_name": job_name,
				"content": comment,
			}
		).insert(ignore_permissions=True)

		return raw_json(
			{"id": doc.name, "comment": comment, "created_by": frappe.session.user, "editable": True}
		)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="add_job_comment API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="Failed to add comment.")


@frappe.whitelist(allow_guest=False)
def delete_job_comment():
	try:
		params = get_request_params()
		comment_id = params.get("id")
		if frappe.db.exists("Communication", comment_id):
			frappe.delete_doc("Communication", comment_id, ignore_permissions=True)
		return raw_json({"message": "Success"})
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="delete_job_comment API Failed", message=frappe.get_traceback())
		ResponseHandler.error(status_code=500, title="Server Error", message="Failed to delete comment.")


@frappe.whitelist(allow_guest=False)
def add_job_video():
	try:
		return raw_json({"message": "Video added", "id": 1})
	except Exception:
		frappe.db.rollback()
		ResponseHandler.error(status_code=500, title="Server Error", message="Failed to add video.")


@frappe.whitelist(allow_guest=False)
def delete_job_video():
	try:
		return raw_json({"message": "Success"})
	except Exception:
		frappe.db.rollback()
		ResponseHandler.error(status_code=500, title="Server Error", message="Failed to delete video.")
