import frappe
from frappe.utils import getdate


def execute_daily_operations():
	"""
	Main daily task to process reoccurring master job templates.
	Handles Daily and Weekly frequency logic.
	"""
	frappe.logger().info("Starting Enviro Scheduled Reoccurring Operations")

	# Fetch all Master templates
	master_jobs = frappe.get_all(
		"Enviro Job Card",
		filters={"is_reoccurring_quote": "YES"},
		fields=[
			"name",
			"source_quotation",
			"type_of_reoccurring",
			"frequency_in_weeks",
			"job_creation_date",
			"monday",
			"tuesday",
			"wednesday",
			"thursday",
			"friday",
			"saturday",
			"sunday",
		],
	)

	today = getdate()
	day_map = {
		0: "monday",
		1: "tuesday",
		2: "wednesday",
		3: "thursday",
		4: "friday",
		5: "saturday",
		6: "sunday",
	}
	today_field = day_map.get(today.weekday())

	for job in master_jobs:
		try:
			# Daily frequency check (based on checkboxes for days of week)
			if job.type_of_reoccurring == "in Daily":
				if not job.get(today_field):
					continue

			# Weekly frequency check (based on weeks count from creation date)
			elif job.type_of_reoccurring == "in Weeks Only":
				if not job.job_creation_date or not job.frequency_in_weeks:
					continue
				delta_days = (today - getdate(job.job_creation_date)).days
				if delta_days <= 0 or delta_days % (job.frequency_in_weeks * 7) != 0:
					continue
			else:
				continue

			frappe.logger().info(f"Triggering clone for master job: {job.name}")
			duplicate_and_schedule(job)
		except Exception as e:
			frappe.log_error(f"Error processing master job {job.name}: {e!s}", "Enviro Cron Error")

	# Batch commit after all operations are queued
	frappe.db.commit()


def duplicate_and_schedule(master_job):
	"""
	Duplicates the source quotation of a master job and creates a new instance.
	Includes duplicate protection to ensure a master job isn't cloned twice on the same day.
	"""
	if not master_job.source_quotation:
		return

	# Duplicate protection using exists() for speed
	if frappe.db.exists(
		"Quotation", {"custom_enviro_job_card": master_job.name, "transaction_date": frappe.utils.today()}
	):
		frappe.logger().info(f"Duplicate protection: Master {master_job.name} already cloned today.")
		return

	original_quote = frappe.get_doc("Quotation", master_job.source_quotation)

	# Clone the Quotation
	new_quote = frappe.copy_doc(original_quote)
	new_quote.transaction_date = frappe.utils.today()
	new_quote.custom_enviro_job_card = master_job.name

	# Reset workflow/approval statuses
	if new_quote.custom_requires_client_approval == 1:
		new_quote.custom_client_approval_status = "Pending"
	else:
		new_quote.custom_client_approval_status = "Not Required"

	new_quote.custom_accounts_approval_status = "Pending"
	new_quote.insert(ignore_permissions=True)

	# Email Pipeline Logic
	if new_quote.custom_requires_client_approval == 1:
		try:
			from enviro.custom_scripts.quotation import send_approval_email

			send_approval_email(new_quote.name)
		except Exception as e:
			frappe.log_error(f"Failed to auto-dispatch clone email: {e!s}")
