import json

import frappe
from frappe.utils import get_url


def before_save(doc, method=None):
	# Enforce Enviro Job Card linkage
	if getattr(doc, "custom_accounts_approval_status", "") == "Approved":
		if not getattr(doc, "custom_enviro_job_card", None):
			frappe.throw(
				"❌ You must create and link an <b>Enviro Job Card</b> before confirming this Quotation internally."
			)

	# If the user checks 'Requires Client Approval'
	if doc.custom_requires_client_approval:
		# Check if the client has already signed the web form or clicked the email button
		if doc.custom_customer_signature or doc.custom_client_approval_status == "Approved":
			# Client has signed it!
			doc.custom_client_approval_status = "Approved"

			# Now it proceeds to the Accounts Review stage (if not already approved)
			if doc.custom_accounts_approval_status not in ["Approved", "Rejected"]:
				doc.custom_accounts_approval_status = "Pending"

		else:
			# Client hasn't signed it yet
			doc.custom_client_approval_status = "Pending"
			# Explicitly blank out the accounts status so they know it's not ready for them
			doc.custom_accounts_approval_status = ""

	# If the user DOES NOT require client approval
	else:
		doc.custom_client_approval_status = "Not Required"

		# It goes straight to the Accounts Review stage
		if doc.custom_accounts_approval_status not in ["Approved", "Rejected"]:
			doc.custom_accounts_approval_status = "Pending"

	# 4. RESOURCE AVAILABILITY CHECK (FOR REOCCURRING/INTENDED SCHEDULES)
	if doc.custom_intended_start_date:
		from enviro.enviro.api.scheduling import check_resource_availability

		# Exclude the job already linked to this quotation to avoid self-conflict
		linked_job = frappe.db.get_value(
			"Enviro Job", {"quotation": doc.name, "status": ["!=", "Cancelled"]}, "name"
		)

		check_resource_availability(
			doc.custom_intended_driver,
			doc.custom_intended_vehicle,
			doc.custom_intended_start_date,
			exclude_quote=doc.name,
			exclude_job=linked_job,
		)


def on_update(doc, method=None):
	# AUTO-SPAWN ENVIRO JOB ON APPROVAL
	# We rely on the 'intended' fields set by the dashboard for reoccurring jobs
	if (
		doc.custom_accounts_approval_status == "Approved"
		and doc.custom_intended_start_date
		and not doc.get_db_value("custom_accounts_approval_status") == "Approved"
	):
		spawn_job_from_intent(doc)


def spawn_job_from_intent(doc):
	frappe.logger().info(f"Finalizing job for Quotation: {doc.name} from intended schedule")

	# Check if an 'Allocated' job already exists (created during scheduling)
	job_name = frappe.db.get_value("Enviro Job", {"quotation": doc.name, "status": "Allocated"}, "name")

	if job_name:
		new_job = frappe.get_doc("Enviro Job", job_name)
	else:
		# Fallback: create new if not found
		new_job = frappe.new_doc("Enviro Job")
		new_job.source_job_card = doc.custom_enviro_job_card
		new_job.quotation = doc.name
		new_job.customer = doc.party_name
		new_job.site = doc.custom_site

	# Map intended data (in case they were changed during approval)
	new_job.scheduled_start_date = doc.custom_intended_start_date
	new_job.scheduled_start_time = doc.custom_intended_start_time
	new_job.scheduled_end_date = doc.custom_intended_end_date
	new_job.scheduled_end_time = doc.custom_intended_end_time
	new_job.vehicle = doc.custom_intended_vehicle
	new_job.driver = doc.custom_intended_driver
	new_job.status = "Scheduled"

	# Team Members (JSON parsing)
	if doc.custom_intended_team:
		try:
			team = json.loads(doc.custom_intended_team)
			new_job.set("team_members", [])
			for member in team:
				new_job.append("team_members", {"employee": member})
		except Exception:
			pass

	new_job.save(ignore_permissions=True)

	# CLEAR INTENDED FIELDS TO PREVENT DOUBLE SPAWNING
	frappe.db.set_value(
		"Quotation",
		doc.name,
		{
			"custom_intended_start_date": None,
			"custom_intended_start_time": None,
			"custom_intended_end_date": None,
			"custom_intended_end_time": None,
			"custom_intended_vehicle": None,
			"custom_intended_driver": None,
			"custom_intended_team": None,
		},
		update_modified=False,
	)

	frappe.msgprint(f"✅ Automated: Enviro Job <b>{new_job.name}</b> has been scheduled.")


@frappe.whitelist()
def send_approval_email(docname: str):
	doc = frappe.get_doc("Quotation", docname)

	if not doc.custom_site_email:
		frappe.throw("No Site Email found to send the approval request.")

	if not getattr(doc, "custom_enviro_job_card", None):
		frappe.throw(
			"❌ You must create and link an Enviro Job Card before sending the approval request to the customer."
		)

	# Generate a secure one-time token if one does not exist
	if not doc.custom_approval_token:
		doc.custom_approval_token = frappe.generate_hash(length=32)
		doc.save(ignore_permissions=True)
		frappe.db.commit()  # nosemgrep

	view_link = f"{get_url()}/quote_view?name={doc.name}&token={doc.custom_approval_token}"

	message = f"""
    <div style="font-family: Inter, Arial, sans-serif; max-width: 600px; padding: 25px; border: 1px solid #e5e7eb; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="text-align: center; margin-bottom: 20px;">
            <!-- Dummy Logo Space -->
            <h1 style="color: #0ea5e9; margin: 0; font-size: 24px;">enviro</h1>
        </div>
        <div style="background-color: #0ea5e9; height: 10px; width: 100%; border-radius: 4px;"></div>
        <h2 style="color: #111827; text-align: center; margin-top: 20px;">Enviro Quotation</h2>
        <p style="color: #374151; font-size: 14px; text-align: center; margin-bottom: 30px;">
            This is your most recent quote. Kindly click the button below to access the quote details and optionally customize your site information.
        </p>

        <div style="text-align: center; margin-top: 35px; margin-bottom: 35px;">
            <a href="{view_link}" style="padding: 12px 24px; background-color: #38bdf8; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">View Quote</a>
        </div>

        <p style="color: #6b7280; font-size: 14px; text-align: center; margin-bottom: 0;">Thanks,<br>Team Enviro</p>
    </div>
    """

	frappe.sendmail(
		recipients=[doc.custom_site_email],
		subject=f"Action Required: Quotation {doc.name} Approval",
		message=message,
		reference_doctype="Quotation",
		reference_name=doc.name,
		attachments=[frappe.attach_print(doc.doctype, doc.name, file_name=f"Quotation_{doc.name}")],
		now=True,
	)
	return "Sent"


@frappe.whitelist(allow_guest=True)  # nosemgrep
def submit_quote_approval():
	data = frappe.local.form_dict
	name = data.get("name")
	token = data.get("token")
	action = data.get("action")

	if not frappe.db.exists("Quotation", name):
		return {"status": "error", "message": "Quotation not found"}

	doc = frappe.get_doc("Quotation", name)
	if not doc.custom_approval_token or doc.custom_approval_token != token:
		return {"status": "error", "message": "Invalid or expired token"}

	if action == "reject":
		doc.custom_client_approval_status = "Rejected"
		doc.custom_approval_token = ""
		doc.save(ignore_permissions=True)
		frappe.db.commit()  # nosemgrep
		return {"status": "success", "message": "Rejected"}

	if action == "approve":
		# Handle Site details updates if provided
		site_details = json.loads(data.get("site_details", "{}"))
		if doc.custom_site and site_details:
			site = frappe.get_doc("Site", doc.custom_site)
			if site_details.get("site_name"):
				site.site_name = site_details.get("site_name")
			if site_details.get("site_address"):
				site.site_address = site_details.get("site_address")
			if site_details.get("contact_name"):
				site.site_contact_person = site_details.get("contact_name")
			site.save(ignore_permissions=True)

		# Save Signature
		signature_b64 = data.get("signature")
		if signature_b64:
			import base64

			# The base64 usually starts with data:image/png;base64,...
			if "," in signature_b64:
				signature_b64 = signature_b64.split(",")[1]

			file_doc = frappe.new_doc("File")
			file_doc.file_name = f"signature_{name}.png"
			file_doc.is_private = 1
			file_doc.content = base64.b64decode(signature_b64)
			file_doc.attached_to_doctype = "Quotation"
			file_doc.attached_to_name = name
			file_doc.insert(ignore_permissions=True)

			doc.custom_customer_signature = file_doc.file_url

		doc.custom_client_approval_status = "Approved"
		doc.custom_accounts_approval_status = "Pending"
		doc.custom_approval_token = ""
		doc.save(ignore_permissions=True)
		frappe.db.commit()  # nosemgrep
		return {"status": "success", "message": "Approved"}

	return {"status": "error", "message": "Unknown action"}


@frappe.whitelist()
def submit_quotation(name):
	doc = frappe.get_doc("Quotation", name)
	doc.submit()
	return "Submitted"


@frappe.whitelist()
def make_enviro_job_card(source_name: str, target_doc: dict | None = None):
	from frappe.model.mapper import get_mapped_doc

	def build_metadata(source, target, source_parent=None):
		# 1. Safely pull Site Metadata
		if target.site:
			site_fields = frappe.db.get_value(
				"Site",
				target.site,
				[
					"site_name",
					"site_address",
					"site_postcode",
					"site_contact_person",
					"site_phone",
					"site_contact_mobile",
					"site_email_address",
					"company_phone",
					"company_email",
				],
				as_dict=True,
			)
			if site_fields:
				target.site_name = site_fields.site_name
				target.site_address = site_fields.site_address
				target.site_postcode = site_fields.site_postcode
				target.site_contact_name = site_fields.site_contact_person
				target.site_contact_phone = site_fields.site_phone
				target.site_contact_mob = site_fields.site_contact_mobile
				target.site_contact_email = site_fields.site_email_address
				target.company_contact_phone = site_fields.company_phone
				target.company_contact_email = site_fields.company_email

		# 2. Safely pull Customer Metadata
		if target.customer:
			cust_fields = frappe.db.get_value(
				"Customer", target.customer, ["customer_name", "customer_primary_address"], as_dict=True
			)
			if cust_fields:
				# Overwrite "company_name" with the Customer Name (not the ERPNext Tenant)
				target.company_name = cust_fields.customer_name
				target.company_address = cust_fields.customer_primary_address

	doclist = get_mapped_doc(
		"Quotation",
		source_name,
		{
			"Quotation": {
				"doctype": "Enviro Job Card",
				"field_map": {"name": "source_quotation", "party_name": "customer", "custom_site": "site"},
				"postprocess": build_metadata,
			}
		},
		target_doc,
	)

	return doclist
