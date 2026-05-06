import csv

import frappe
from frappe.utils.password import update_password


def generate_user_report(output_path=None):
	"""
	Generates a structured CSV report of all enabled System Users.
	"""
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Administrator"]},
		fields=["name", "first_name", "last_name"],
	)

	if not output_path:
		output_path = frappe.get_site_path("public", "files", "enviro_user_report.csv")

	generic_roles = ["Employee", "All", "Guest", "Desk User", "Desk Access", "System Manager", "Superadmin"]

	results = []
	for u in users:
		all_roles = frappe.get_roles(u.name)
		primary_role = next((role for role in all_roles if role not in generic_roles), "Employee")

		results.append(
			{
				"Username": u.name,
				"Primary Role": primary_role,
				"Full Name": f"{u.first_name} {u.last_name or ''}".strip(),
				"Roles": ", ".join(all_roles),
			}
		)

	results.sort(key=lambda x: x["Primary Role"])

	with open(output_path, "w", newline="") as csvfile:
		fieldnames = ["Username", "Primary Role", "Full Name", "Roles"]
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(results)

	return output_path


@frappe.whitelist()
def reset_test_passwords(password="Enviro@Test#2024"):
	"""
	Resets passwords for all non-admin system users for testing purposes.
	Authorized for System Managers only.
	"""
	frappe.only_for("System Manager")

	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Administrator"]},
		pluck="name",
	)

	for user in users:
		update_password(user, password)

	frappe.db.commit()
	return f"Passwords reset for {len(users)} users."


if __name__ == "__main__":
	print(generate_user_report())
