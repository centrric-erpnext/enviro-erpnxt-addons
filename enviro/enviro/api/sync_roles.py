import frappe

from enviro.enviro.api.permissions import MATRIX


def run():
	roles = list(MATRIX.keys())
	# Clear all first
	frappe.db.set_value("Role", {}, "custom_enviro_role", 0)

	# Set for MATRIX roles
	updated = 0
	for role_name in roles:
		if frappe.db.exists("Role", role_name):
			frappe.db.set_value("Role", role_name, "custom_enviro_role", 1)
			updated += 1

	frappe.db.commit()
	print(f"Successfully updated {updated} Enviro Roles based on permission matrix.")


@frappe.whitelist()
def set_enviro_role(docnames, status):
	import json

	if isinstance(docnames, str):
		docnames = json.loads(docnames)

	for name in docnames:
		frappe.db.set_value("Role", name, "custom_enviro_role", int(status))

	frappe.db.commit()
