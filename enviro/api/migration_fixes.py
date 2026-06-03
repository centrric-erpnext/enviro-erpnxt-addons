import os

import frappe


@frappe.whitelist(allow_guest=False)
def run_all():
	"""Run all post-migration fixes. Can be executed via bench or API."""
	if not frappe.session.user == "Administrator":
		frappe.throw("Only Administrator can run migration fixes.")

	print("Starting post-migration cleanup...")

	# 1. Fix Naming Series for legacy employees
	frappe.db.sql("""
        UPDATE `tabEmployee`
        SET naming_series = 'HR-EMP-'
        WHERE naming_series IS NULL OR naming_series = ''
    """)
	print("Fixed Naming Series for legacy employees.")

	# 2. Fix Image URLs (Prepend /files/ if legacy path)
	frappe.db.sql("""
        UPDATE `tabEmployee`
        SET image = CONCAT('/', image)
        WHERE image IS NOT NULL
          AND image != ''
          AND image NOT LIKE '/%'
          AND image NOT LIKE 'http%'
    """)
	frappe.db.sql("""
        UPDATE `tabEmployee`
        SET image = REPLACE(image, '/uploads/', '/files/uploads/')
        WHERE image LIKE '/uploads/%'
    """)
	frappe.db.sql("""
        UPDATE `tabEmployee`
        SET image = REPLACE(image, '/default/', '/files/default/')
        WHERE image LIKE '/default/%'
    """)
	print("Fixed legacy image URL formatting.")

	# 3. Clean up missing images to prevent FileNotFoundError
	employees_with_images = frappe.db.sql(
		"""
        SELECT name, image FROM `tabEmployee` WHERE image IS NOT NULL AND image != ''
    """,
		as_dict=True,
	)

	missing_count = 0
	for emp in employees_with_images:
		image_path = emp.image
		if image_path.startswith("/files/"):
			image_path = image_path.replace("/files/", "")

		full_path = frappe.get_site_path("public", "files", image_path)

		if not os.path.exists(full_path):
			frappe.db.set_value("Employee", emp.name, "image", None, update_modified=False)
			missing_count += 1
	print(f"Cleared {missing_count} missing images to prevent server crashes.")

	# 4. Fix Missing Notification Settings
	users = frappe.get_all("User", pluck="name")
	notif_count = 0
	for user in users:
		if not frappe.db.exists("Notification Settings", user):
			doc = frappe.new_doc("Notification Settings")
			doc.name = user
			doc.insert(ignore_permissions=True, ignore_mandatory=True)
			notif_count += 1
	print(f"Created {notif_count} missing Notification Settings.")

	# 5. Map Custom Position Title to System Roles
	employees = frappe.get_all(
		"Employee",
		filters={"user_id": ["!=", ""], "custom_position_title": ["!=", ""]},
		fields=["name", "user_id", "custom_position_title"],
	)
	valid_roles = frappe.get_all("Role", pluck="name")
	role_count = 0

	for emp in employees:
		user_id = emp.user_id
		role = emp.custom_position_title

		if role in valid_roles and frappe.db.exists("User", user_id):
			user = frappe.get_doc("User", user_id)
			roles_to_add = ["Desk User", "Employee", role]

			if role in ["Accounts Staff", "Accounts Manager", "Enviro Accounts"]:
				roles_to_add.extend(["Accounts User", "Sales User"])
			elif role in ["Sales Staff", "Sales Manager", "Enviro Sales"]:
				roles_to_add.append("Sales User")

			added = False

			for r in roles_to_add:
				if not frappe.db.exists("Has Role", {"parent": user_id, "role": r}):
					user.append("roles", {"role": r})
					added = True

			if added:
				user.save(ignore_permissions=True)
				role_count += 1

	print(f"Mapped Workspace Roles for {role_count} imported users.")

	# 6. Generate Team Folders Master Structure
	folders = [
		"Annual Leave Form",
		"Asset, Tool, Uniform Register",
		"Code of Conduct",
		"Doctors Certificates",
		"Employee Contract EW Services",
		"Employee Contract Enviro Waste",
		"Employee Health Form",
		"Employee Update Form",
		"Inductions",
		"Interlink Email Set Up",
		"Leave Applications",
		"Licences",
		"Police Checks",
		"Position Description",
		"Standard Operating Procedure (SOP)",
		"Superannuation Form",
		"Tax Declaration Form",
		"Timesheet",
	]
	folder_count = 0
	for folder in folders:
		if not frappe.db.exists("Enviro Team Folder", folder):
			doc = frappe.new_doc("Enviro Team Folder")
			doc.folder_name = folder
			doc.is_system_folder = 1
			doc.insert(ignore_permissions=True)
			folder_count += 1
	print(f"Generated {folder_count} Master Team Folders.")

	frappe.db.commit()
	print("Post-migration cleanup completed successfully!")
	return "Cleanup Complete"
