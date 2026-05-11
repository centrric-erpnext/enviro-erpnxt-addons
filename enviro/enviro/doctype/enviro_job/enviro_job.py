import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class EnviroJob(Document):
	"""
	Represents a physical execution of a waste management job.
	Includes lifecycle tracking (GPS, timestamps, photos) and resource validation.
	"""

	def validate(self):
		"""Triggers hard database validation for driver/vehicle availability."""
		self.check_availability()
		self.fetch_waste_type()

	def fetch_waste_type(self):
		"""Aggregates all unique waste types from the linked quotation's items."""
		if self.quotation:
			# Use SQL to aggregate to handle multiple items efficiently
			waste_types = frappe.db.sql(
				"""
				SELECT DISTINCT custom_waste_type
				FROM `tabQuotation Item`
				WHERE parent = %s AND custom_waste_type IS NOT NULL AND custom_waste_type != ''
			""",
				self.quotation,
				pluck=True,
			)

			if waste_types:
				# Store as a sorted comma-separated string
				self.custom_waste_type = ", ".join(sorted(waste_types))
			else:
				self.custom_waste_type = ""

	def check_availability(self):
		"""
		Prevents double-booking by checking both other Jobs and pending Quotations.
		Intelligently ignores its own linked Quotation to allow reoccurring scheduling.
		"""
		if self.status == "Cancelled":
			return

		if not self.scheduled_start_date:
			return

		# Check Driver Availability
		if self.driver:
			conflict = frappe.db.exists(
				"Enviro Job",
				{
					"driver": self.driver,
					"scheduled_start_date": self.scheduled_start_date,
					"status": ["!=", "Cancelled"],
					"name": ["!=", self.name],
				},
			)
			if conflict:
				frappe.throw(
					_("Driver {0} is already scheduled for job {1} on {2}").format(
						self.driver, conflict, self.scheduled_start_date
					)
				)

			# Also check pending Quotations (Intended schedules)
			q_conflict = frappe.db.exists(
				"Quotation",
				{
					"custom_intended_driver": self.driver,
					"custom_intended_start_date": self.scheduled_start_date,
					"docstatus": ["<", 2],
					"status": ["not in", ["Cancelled", "Lost"]],
					"name": ["!=", self.quotation] if self.quotation else ["is", "set"],
				},
			)
			if q_conflict:
				frappe.throw(
					_("Driver {0} is already reserved for pending Quotation {1} on {2}").format(
						self.driver, q_conflict, self.scheduled_start_date
					)
				)

		# Check Vehicle Availability
		if self.vehicle:
			conflict = frappe.db.exists(
				"Enviro Job",
				{
					"vehicle": self.vehicle,
					"scheduled_start_date": self.scheduled_start_date,
					"status": ["!=", "Cancelled"],
					"name": ["!=", self.name],
				},
			)
			if conflict:
				frappe.throw(
					_("Vehicle {0} is already scheduled for job {1} on {2}").format(
						self.vehicle, conflict, self.scheduled_start_date
					)
				)

			# Also check pending Quotations (Intended schedules)
			q_conflict = frappe.db.exists(
				"Quotation",
				{
					"custom_intended_vehicle": self.vehicle,
					"custom_intended_start_date": self.scheduled_start_date,
					"docstatus": ["<", 2],
					"status": ["not in", ["Cancelled", "Lost"]],
					"name": ["!=", self.quotation] if self.quotation else ["is", "set"],
				},
			)
			if q_conflict:
				frappe.throw(
					_("Vehicle {0} is already reserved for pending Quotation {1} on {2}").format(
						self.vehicle, q_conflict, self.scheduled_start_date
					)
				)


@frappe.whitelist()
def depart_facility(job_id: str, timestamp: str | None = None):
	job = frappe.get_doc("Enviro Job", job_id)
	job.status = "In Transit"
	job.depart_facility_time = get_datetime(timestamp) if timestamp else now_datetime()
	job.save(ignore_permissions=True)
	return job.status


@frappe.whitelist()
def start_job(job_id: str, pre_image: str | None = None):
	# Automatic timestamp for work start (verified by photo)
	job = frappe.get_doc("Enviro Job", job_id)
	job.status = "On Site"
	job.job_started_time = now_datetime()
	if pre_image:
		job.pre_job_image = pre_image
	job.save(ignore_permissions=True)
	return job.status


@frappe.whitelist()
def arrive_at_depot(job_id: str, timestamp: str | None = None):
	job = frappe.get_doc("Enviro Job", job_id)
	job.arrive_depot_time = get_datetime(timestamp) if timestamp else now_datetime()
	job.save(ignore_permissions=True)
	return job.status


@frappe.whitelist()
def depart_depot(job_id: str, timestamp: str | None = None):
	job = frappe.get_doc("Enviro Job", job_id)
	job.depart_depot_time = get_datetime(timestamp) if timestamp else now_datetime()
	job.save(ignore_permissions=True)
	return job.status


@frappe.whitelist()
def finish_job(job_id: str, post_image: str | None = None, signature: str | None = None):
	# Automatic timestamp for work finish (verified by photo/signature)
	job = frappe.get_doc("Enviro Job", job_id)
	job.job_finished_time = now_datetime()
	if post_image:
		job.post_job_image = post_image
	if signature:
		job.contact_signature = signature
	job.save(ignore_permissions=True)
	return job.status


@frappe.whitelist()
def arrive_at_facility(job_id: str, timestamp: str | None = None):
	job = frappe.get_doc("Enviro Job", job_id)
	job.status = "Completed"
	job.arrive_facility_time = get_datetime(timestamp) if timestamp else now_datetime()
	job.save(ignore_permissions=True)
	return job.status


# Compatibility helpers
@frappe.whitelist()
def arrive_on_site(job_id: str):
	job = frappe.get_doc("Enviro Job", job_id)
	job.status = "On Site"
	job.save(ignore_permissions=True)
	return job.status


@frappe.whitelist()
def complete_job(job_id: str):
	job = frappe.get_doc("Enviro Job", job_id)
	job.status = "Completed"
	job.save(ignore_permissions=True)
	return job.status
