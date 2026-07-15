import frappe


def execute():
	"""
	Restore core Frappe default permissions for Employee, Role, and User
	by deleting the overriding Custom DocPerm records.
	"""
	core_doctypes = ["Employee", "Role", "User"]

	for doctype in core_doctypes:
		frappe.db.delete("Custom DocPerm", {"parent": doctype})

	frappe.clear_cache()
