import frappe


def fix_user_permissions():
	user = frappe.get_doc("User", "lifiqphysique@gmail.com")
	roles_to_add = ["Sales User", "Accounts User"]

	for r in roles_to_add:
		if not frappe.db.exists("Has Role", {"parent": user.name, "role": r}):
			user.append("roles", {"role": r})

	user.save(ignore_permissions=True)
	frappe.db.commit()
	print("Added standard Sales/Accounts roles to lifiqphysique@gmail.com")
