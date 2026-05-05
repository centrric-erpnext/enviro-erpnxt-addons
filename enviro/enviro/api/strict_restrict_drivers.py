import frappe


def strict_restrict_drivers():
	# 1. Disable Desk Access for virtual/generic roles
	# 'All' and 'Desk User' are often assigned automatically and give desk access
	for r_name in ["All", "Desk User"]:
		if frappe.db.exists("Role", r_name):
			role = frappe.get_doc("Role", r_name)
			role.desk_access = 0
			role.save(ignore_permissions=True)
			print(f"Disabled Desk Access for {r_name}")

	# 2. Identify Driver/Mobile roles
	driver_roles = [
		"Driver Factory Hand (Mobile)",
		"Driver Factory Hand (Web)",
		"Driver Liquid Waste Technician (Mobile)",
		"Driver Liquid Waste Technician (Web)",
	]

	# Ensure these roles themselves have desk_access = 0
	for dr in driver_roles:
		if frappe.db.exists("Role", dr):
			role = frappe.get_doc("Role", dr)
			role.desk_access = 0
			role.save(ignore_permissions=True)
			print(f"Verified {dr} has no desk access")

	# 3. Identify Users with these roles
	# We filter by parenttype='User' to avoid accidental matches
	users = frappe.get_all(
		"Has Role", filters={"role": ["in", driver_roles], "parenttype": "User"}, pluck="parent"
	)
	users = list(set(users))  # Unique users

	roles_to_remove = ["Employee", "Desk User"]

	for user_email in users:
		if user_email == "Administrator":
			continue

		if not frappe.db.exists("User", user_email):
			print(f"Skipping non-user: {user_email}")
			continue

		user_doc = frappe.get_doc("User", user_email)
		removed = []
		new_roles = []
		for r in user_doc.roles:
			if r.role not in roles_to_remove:
				new_roles.append(r)
			else:
				removed.append(r.role)

		if removed:
			user_doc.roles = new_roles
			user_doc.save(ignore_permissions=True)
			print(f"Removed {removed} from {user_email}")

	frappe.db.commit()


if __name__ == "__main__":
	strict_restrict_drivers()
