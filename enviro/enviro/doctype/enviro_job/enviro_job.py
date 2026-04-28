import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class EnviroJob(Document):
	pass


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
