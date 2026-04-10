import frappe


def execute():
	# Check if there are any standard workflows on Quotation
	workflows = frappe.get_all(
		"Workflow", filters={"document_type": "Quotation"}, fields=["name", "is_active"]
	)
	print("Workflows on Quotation: ", workflows)

	# Let's also check for custom fields on Quotation
	custom_fields = frappe.get_all(
		"Custom Field", filters={"dt": "Quotation"}, fields=["fieldname", "fieldtype", "label"]
	)
	print("Custom Fields on Quotation: ")
	for cf in custom_fields:
		print(f" - {cf.fieldname} ({cf.fieldtype}): {cf.label}")
