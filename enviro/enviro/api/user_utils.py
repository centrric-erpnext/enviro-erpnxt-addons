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


@frappe.whitelist()
def get_sales_employees(doctype, txt, searchfield, start, page_len, filters):
	"""Standard search query for employees who are Sales Staff or Managers."""
	user_ids = frappe.get_all(
		"Has Role", filters={"role": ["in", ["Sales Staff", "Manager"]]}, pluck="parent"
	)
	user_ids = list(set(user_ids))

	if not user_ids:
		return []

	conditions = {"user_id": ["in", user_ids], "status": "Active"}

	employees = frappe.get_all("Employee", filters=conditions, fields=["name", "employee_name"])

	result = []
	safe_txt = (txt or "").lower()
	for emp in employees:
		if safe_txt in emp.name.lower() or safe_txt in str(emp.employee_name or "").lower():
			result.append([emp.name, emp.employee_name or ""])

	return result


@frappe.whitelist()
def get_current_employee():
	"""Returns the employee ID for the current logged-in user."""
	return frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")


if __name__ == "__main__":
	print(generate_user_report())
