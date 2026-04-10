import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.exists("DocType", "Enviro Job"):
		doc = frappe.new_doc("DocType")
		doc.name = "Enviro Job"
		doc.module = "Enviro"
		doc.custom = 1
		doc.autoname = "format:ENV-JOB-{YYYY}-{MM}-{#####}"
		doc.naming_rule = "Expression"

		doc.append(
			"fields",
			{
				"fieldname": "source_job_card",
				"fieldtype": "Link",
				"options": "Enviro Job Card",
				"label": "Source Job Card",
			},
		)
		doc.append(
			"fields",
			{
				"fieldname": "quotation",
				"fieldtype": "Link",
				"options": "Quotation",
				"label": "Source Quotation",
			},
		)
		doc.append(
			"fields",
			{
				"fieldname": "customer",
				"fieldtype": "Link",
				"options": "Customer",
				"label": "Customer",
				"fetch_from": "quotation.customer_name",
			},
		)
		doc.append("fields", {"fieldname": "site", "fieldtype": "Link", "options": "Site", "label": "Site"})

		doc.append(
			"fields",
			{"fieldname": "sb_schedule", "fieldtype": "Section Break", "label": "Schedule & Dispatch"},
		)
		doc.append(
			"fields",
			{"fieldname": "scheduled_start_date", "fieldtype": "Date", "label": "Scheduled Start Date"},
		)
		doc.append(
			"fields",
			{"fieldname": "scheduled_start_time", "fieldtype": "Time", "label": "Scheduled Start Time"},
		)
		doc.append("fields", {"fieldname": "cb_end", "fieldtype": "Column Break"})
		doc.append(
			"fields", {"fieldname": "scheduled_end_date", "fieldtype": "Date", "label": "Scheduled End Date"}
		)
		doc.append(
			"fields", {"fieldname": "scheduled_end_time", "fieldtype": "Time", "label": "Scheduled End Time"}
		)

		doc.append("fields", {"fieldname": "sb_alloc", "fieldtype": "Section Break", "label": "Allocation"})
		doc.append(
			"fields", {"fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "label": "Vehicle"}
		)
		doc.append(
			"fields",
			{"fieldname": "driver", "fieldtype": "Link", "options": "Employee", "label": "Primary Driver"},
		)
		doc.append(
			"fields",
			{
				"fieldname": "team_members",
				"fieldtype": "Table MultiSelect",
				"options": "Enviro Job Team Member",
				"label": "Additional Team",
			},
		)

		doc.append("fields", {"fieldname": "sb_status", "fieldtype": "Section Break", "label": "Tracking"})
		doc.append(
			"fields",
			{
				"fieldname": "status",
				"fieldtype": "Select",
				"label": "Status",
				"options": "Scheduled\nIn Transit\nOn Site\nCompleted\nCancelled",
				"default": "Scheduled",
			},
		)

		doc.permissions = [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
		doc.insert(ignore_permissions=True)
		print("Created Enviro Job Doctype!")
