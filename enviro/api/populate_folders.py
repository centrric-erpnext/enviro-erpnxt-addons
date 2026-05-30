import frappe


@frappe.whitelist()
def populate_team_folders():
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

	count = 0
	for folder in folders:
		if not frappe.db.exists("Enviro Team Folder", folder):
			doc = frappe.new_doc("Enviro Team Folder")
			doc.folder_name = folder
			doc.is_system_folder = 1
			doc.insert(ignore_permissions=True)
			count += 1
			print(f"Folder '{folder}' created.")
		else:
			print(f"Folder '{folder}' already exists.")

	frappe.db.commit()
	return f"Created {count} missing Team Folders."


if __name__ == "__main__":
	populate_team_folders()
