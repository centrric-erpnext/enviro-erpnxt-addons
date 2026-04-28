import frappe
from frappe.utils import getdate


def execute_daily_operations():
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
	# monday=0, ..., sunday=6
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
			if job.type_of_reoccurring == "in Daily":
				if not job.get(today_field):
					continue
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


def duplicate_and_schedule(master_job):
	# Retrieve Source Quotation
	if not master_job.source_quotation:
		return

	# 0. Duplicate protection
	existing_quote = frappe.db.get_all(
		"Quotation",
		filters={"custom_enviro_job_card": master_job.name, "transaction_date": frappe.utils.today()},
	)
	if existing_quote:
		frappe.logger().info(f"Duplicate protection: Master {master_job.name} already cloned today.")
		return

	original_quote = frappe.get_doc("Quotation", master_job.source_quotation)

	# 1. Duplicate Quotation
	new_quote = frappe.copy_doc(original_quote)
	new_quote.transaction_date = frappe.utils.today()

	# Link the newly generated quote directly back to the original Old Master Job Card!
	new_quote.custom_enviro_job_card = master_job.name

	# We must reset statuses so it hits the workflow normally
	if new_quote.custom_requires_client_approval == 1:
		new_quote.custom_client_approval_status = "Pending"
	else:
		new_quote.custom_client_approval_status = "Not Required"

	new_quote.custom_accounts_approval_status = "Pending"
	new_quote.insert(ignore_permissions=True)

	# Commit immediately so the DB has it
	frappe.db.commit()

	# 2. Email Pipeline Logic
	if new_quote.custom_requires_client_approval == 1:
		try:
			from enviro.custom_scripts.quotation import send_approval_email

			send_approval_email(new_quote.name)
		except Exception as e:
			frappe.log_error(f"Failed to auto-dispatch clone email: {e!s}")
