import os

import frappe


def update_custom_html_block():
	script_path = "/home/midhul/frappe-bench/apps/enviro/enviro/enviro/api/new_block_script.js"
	if not os.path.exists(script_path):
		print(f"File {script_path} not found.")
		return

	with open(script_path) as f:
		script_content = f.read()

	block_name = "Enviro Employee Profile"
	if frappe.db.exists("Custom HTML Block", block_name):
		doc = frappe.get_doc("Custom HTML Block", block_name)
		doc.script = script_content

		# Ensure relevant roles have access
		target_roles = ["Administrator", "Superadmin", "Director", "System Manager", "HR Manager"]
		doc.set("roles", [])
		for role in target_roles:
			if frappe.db.exists("Role", role):
				doc.append("roles", {"role": role})

		doc.save()
		frappe.db.commit()
		print(f"Custom HTML Block '{block_name}' updated with roles.")
	else:
		print(f"Custom HTML Block '{block_name}' not found.")


if __name__ == "__main__":
	update_custom_html_block()
