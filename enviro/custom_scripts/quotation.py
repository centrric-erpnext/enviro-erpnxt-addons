import json

import frappe
from frappe.utils import get_url


def before_save(doc, method=None):
	"""
	Custom logic for Quotation lifecycle:
	1. Enforces Enviro Job Card linkage.
	2. Handles Client and Accounts approval state machine.
	3. Performs resource availability validation for reoccurring jobs.
	"""
	# Enforce Enviro Job Card linkage
	if getattr(doc, "custom_accounts_approval_status", "") == "Approved":
		if not getattr(doc, "custom_enviro_job_card", None):
			if not getattr(frappe.flags, "in_import", False):
				frappe.throw(
					"❌ You must create and link an <b>Enviro Job Card</b> before confirming this Quotation internally."
				)

	# --- PIPELINE STATE MACHINE ---
	# 1. CLIENT APPROVAL
	# If client signature or email approval happened:
	if doc.custom_customer_signature or doc.custom_client_approval_status == "Approved":
		doc.custom_client_approval_status = "Approved"
	# Or if client approval isn't required at all:
	elif not frappe.utils.cint(doc.get("custom_requires_client_approval")):
		doc.custom_client_approval_status = "Approved"
	else:
		doc.custom_client_approval_status = "Pending"

	# 2. SALES TEAM APPROVAL
	if doc.custom_client_approval_status == "Approved":
		if not getattr(doc, "custom_sales_approval_status", None) or doc.custom_sales_approval_status not in [
			"Approved",
			"Rejected",
		]:
			doc.custom_sales_approval_status = "Pending"
	else:
		doc.custom_sales_approval_status = "Pending"

	# 3. ACCOUNTS TEAM APPROVAL
	if getattr(doc, "custom_sales_approval_status", "") == "Approved":
		if doc.custom_accounts_approval_status not in ["Approved", "Rejected"]:
			doc.custom_accounts_approval_status = "Pending"
	else:
		doc.custom_accounts_approval_status = "Not Required"

	# 4. RESOURCE AVAILABILITY CHECK (FOR REOCCURRING/INTENDED SCHEDULES)
	if doc.custom_intended_start_date:
		from enviro.api.scheduling import check_resource_availability

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
def send_approval_email(docname, cc=None, bcc=None, custom_message=None):
	frappe.enqueue(
		"enviro.custom_scripts.quotation.send_approval_email_background",
		docname=docname,
		cc=cc,
		bcc=bcc,
		custom_message=custom_message,
		queue="short",
		timeout=300,
	)
	return "Queued"


def send_approval_email_background(docname, cc=None, bcc=None, custom_message=None):
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

	if custom_message:
		custom_message_html = f'<p style="color: #374151; font-size: 14px; text-align: left; margin-bottom: 20px; white-space: pre-wrap; padding: 15px; background-color: #f3f4f6; border-radius: 6px;">{custom_message}</p>'
	else:
		custom_message_html = ""

	message = f"""
    <div style="font-family: Inter, Arial, sans-serif; max-width: 600px; padding: 25px; border: 1px solid #e5e7eb; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="text-align: center; margin-bottom: 20px;">
            <!-- Dummy Logo Space -->
            <h1 style="color: #0ea5e9; margin: 0; font-size: 24px;">enviro</h1>
        </div>
        <div style="background-color: #0ea5e9; height: 10px; width: 100%; border-radius: 4px;"></div>
        <h2 style="color: #111827; text-align: center; margin-top: 20px;">Enviro Quotation</h2>
        {custom_message_html}
        <p style="color: #374151; font-size: 14px; text-align: center; margin-bottom: 30px;">
            This is your most recent quote. Kindly click the button below to access the quote details and optionally customize your site information.
        </p>

        <div style="text-align: center; margin-top: 35px; margin-bottom: 35px;">
            <a href="{view_link}" style="padding: 12px 24px; background-color: #38bdf8; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">View Quote</a>
        </div>

        <p style="color: #6b7280; font-size: 14px; text-align: center; margin-bottom: 0;">Thanks,<br>Team Enviro</p>
    </div>
    """

	cc_list = [email.strip() for email in cc.split(",") if email.strip()] if cc else []
	bcc_list = [email.strip() for email in bcc.split(",") if email.strip()] if bcc else []

	frappe.sendmail(
		recipients=[doc.custom_site_email],
		cc=cc_list,
		bcc=bcc_list,
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
			if site_details.get("site_address"):
				site.site_address = site_details.get("site_address")
			if site_details.get("contact_name"):
				site.site_contact_person = site_details.get("contact_name")
			if site_details.get("site_email"):
				site.site_email_address = site_details.get("site_email")
			if site_details.get("site_phone"):
				site.site_phone = site_details.get("site_phone")
			site.save(ignore_permissions=True)

			# PROPAGATE TO ENVIRO JOB CARD & JOBS
			if getattr(doc, "custom_enviro_job_card", None):
				frappe.db.set_value(
					"Enviro Job Card",
					doc.custom_enviro_job_card,
					{
						"site_name": site.site_name,
						"site_address": site.site_address,
						"site_contact_name": site.site_contact_person,
						"site_contact_phone": site.site_phone,
						"site_contact_email": site.site_email_address,
					},
					update_modified=True,
				)

			# PROPAGATE TO ACTIVE JOBS
			active_jobs = frappe.get_all(
				"Enviro Job",
				filters={
					"quotation": name,
					"status": ["in", ["Scheduled", "In Transit", "On Site"]],
				},
				pluck="name",
			)
			for job_name in active_jobs:
				frappe.db.set_value(
					"Enviro Job",
					job_name,
					{
						"site_name": site.site_name,
						"site_address": site.site_address,
						"site_contact_name": site.site_contact_person,
						"site_contact_phone": site.site_phone,
						"site_contact_email": site.site_email_address,
					},
					update_modified=True,
				)

		# Save Signature
		signature_b64 = data.get("signature")
		if signature_b64:
			from enviro.utils.api_utils import save_signature

			file_url = save_signature("Quotation", name, signature_b64)
			doc.custom_customer_signature = file_url

			# PROPAGATE SIGNATURE
			if getattr(doc, "custom_enviro_job_card", None):
				frappe.db.set_value(
					"Enviro Job Card",
					doc.custom_enviro_job_card,
					"custom_customer_signature",
					file_url,
				)

			active_jobs = frappe.get_all(
				"Enviro Job",
				filters={
					"quotation": name,
					"status": ["in", ["Scheduled", "In Transit", "On Site"]],
				},
				pluck="name",
			)
			for job_name in active_jobs:
				frappe.db.set_value(
					"Enviro Job",
					job_name,
					"contact_signature",
					file_url,
					update_modified=True,
				)

		doc.custom_client_approval_status = "Approved"
		doc.custom_sales_approval_status = "Pending"
		doc.custom_accounts_approval_status = "Not Required"
		doc.custom_approval_token = ""
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "message": "Approved"}

	return {"status": "error", "message": "Unknown action"}


@frappe.whitelist()
def submit_quotation(name):
	doc = frappe.get_doc("Quotation", name)
	doc.custom_sales_approval_status = "Approved"
	doc.save(ignore_permissions=True)
	doc.submit()
	return "Submitted"


@frappe.whitelist()
def make_enviro_job_card(source_name, target_doc=None):
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
					"industry_type",
					"induction_type",
					"sales_person",
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
				target.industry_type = site_fields.industry_type
				target.induction_type = site_fields.induction_type
				target.sales_person = site_fields.sales_person

		# 2. Safely pull Customer Metadata
		if target.customer:
			cust_fields = frappe.db.get_value(
				"Customer",
				target.customer,
				["customer_name", "customer_primary_address"],
				as_dict=True,
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
				"field_map": {
					"name": "source_quotation",
					"party_name": "customer",
					"custom_site": "site",
				},
				"postprocess": build_metadata,
			}
		},
		target_doc,
	)

	return doclist


@frappe.whitelist()
def approve_on_behalf_of_client(name):
	doc = frappe.get_doc("Quotation", name)
	doc.custom_client_approval_status = "Approved"
	doc.add_comment(
		"Comment",
		f"Client Approval was manually bypassed/approved internally by {frappe.session.user} on behalf of the client.",
	)
	doc.save(ignore_permissions=True)
	return "Approved"


@frappe.whitelist()
def on_submit(doc, method=None):
	if getattr(doc, "custom_site", None):
		site = frappe.get_doc("Site", doc.custom_site)
		if site.site_type == "Temporary Site":
			site_name = site.site_name or site.name

			# Check if customer already exists with this name
			if frappe.db.exists("Customer", site_name):
				customer_name = site_name
			else:
				# Create a permanent customer from this temporary site
				new_cust = frappe.get_doc(
					{
						"doctype": "Customer",
						"customer_name": site_name,
						"customer_group": "Commercial",
						"territory": "Australia",
						"email_id": site.company_email,
						"mobile_no": site.company_phone,
					}
				)
				new_cust.insert(ignore_permissions=True)
				customer_name = new_cust.name

			# Upgrade the site to Permanent and link to the Customer
			site.site_type = "Permanent Site"
			site.customer = customer_name
			site.save(ignore_permissions=True)

			# Set Quotation's party to the real customer too
			doc.db_set("party_name", customer_name)

			frappe.msgprint(
				f"The attached site {site.name} has been upgraded to a Permanent Site and linked to Company {customer_name}!",
				indicator="green",
				title="Site Upgraded 🚀",
			)
