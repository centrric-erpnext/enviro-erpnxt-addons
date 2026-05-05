import csv

import frappe


def generate_structured_user_list():
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Administrator"]},
		fields=["name", "first_name", "last_name"],
	)

	test_password = "Enviro@Test#2024"
	output_path = "/home/midhul/frappe-bench/apps/enviro/enviro/enviro/api/enviro_test_users_structured.csv"

	# Generic roles to ignore when finding the "Primary Role"
	generic_roles = ["Employee", "All", "Guest", "Desk User", "Desk Access", "System Manager", "Superadmin"]

	results = []
	for u in users:
		all_roles = frappe.get_roles(u.name)

		# Determine Primary Role (first one not in generic list)
		primary_role = "Employee"  # Default
		for role in all_roles:
			if role not in generic_roles:
				primary_role = role
				break

		results.append(
			{
				"Username": u.name,
				"Password": test_password,
				"Primary Role": primary_role,
				"Full Name": f"{u.first_name} {u.last_name or ''}".strip(),
			}
		)

	# Sort by Primary Role to make it more structured
	results.sort(key=lambda x: x["Primary Role"])

	with open(output_path, "w", newline="") as csvfile:
		fieldnames = ["Username", "Password", "Primary Role", "Full Name"]
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(results)

	print(f"Structured user list generated at {output_path}")


if __name__ == "__main__":
	generate_structured_user_list()
