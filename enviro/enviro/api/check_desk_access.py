import frappe


def check_user_desk_access():
	user_email = "driver.lw.web@enviro.com"
	if not frappe.db.exists("User", user_email):
		print(f"User {user_email} not found")
		return

	roles = frappe.get_roles(user_email)
	print(f"Roles for {user_email}:")
	for r in roles:
		desk_access = frappe.db.get_value("Role", r, "desk_access")
		print(f"  - {r}: Desk Access = {desk_access}")


if __name__ == "__main__":
	check_user_desk_access()
