import frappe


def execute():
	# Check fields in Site doctype
	site_fields = frappe.get_all(
		"DocField", filters={"parent": "Site"}, fields=["fieldname", "fieldtype", "label"]
	)
	print("Fields in Site DocType:")
	for f in site_fields:
		print(f" - {f.fieldname} ({f.fieldtype}): {f.label}")

	# Check custom fields in Site doctype
	site_custom = frappe.get_all(
		"Custom Field", filters={"dt": "Site"}, fields=["fieldname", "fieldtype", "label"]
	)
	for f in site_custom:
		print(f" - {f.fieldname} [{f.fieldtype}]: {f.label}")
