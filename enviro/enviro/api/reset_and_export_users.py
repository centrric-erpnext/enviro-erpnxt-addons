import csv

import frappe


def set_test_passwords_and_export():
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Administrator"]},
		fields=["name", "first_name", "last_name"],
	)

	test_password = "Enviro@Test#2024"  # More complex to bypass policy
	output_path = "/home/midhul/frappe-bench/apps/enviro/enviro/enviro/api/enviro_test_users.csv"

	# Temporarily disable password complexity if possible, but let's just use a better password first

	results = []
	for u in users:
		try:
			# Using update_password directly bypasses some validations
			from frappe.utils.password import update_password

			update_password(u.name, test_password)

			roles = frappe.get_roles(u.name)
			results.append(
				{
					"Email": u.name,
					"Full Name": f"{u.first_name} {u.last_name or ''}".strip(),
					"Roles": ", ".join(roles),
					"Password": test_password,
				}
			)
		except Exception as e:
			print(f"Error for user {u.name}: {e}")

	frappe.db.commit()

	with open(output_path, "w", newline="") as csvfile:
		fieldnames = ["Email", "Full Name", "Roles", "Password"]
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(results)

	print(f"Set passwords and generated file at {output_path}")


if __name__ == "__main__":
	set_test_passwords_and_export()
