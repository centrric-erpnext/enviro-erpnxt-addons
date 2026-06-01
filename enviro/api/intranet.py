import frappe
from frappe import _


@frappe.whitelist()
def get_intranet_data():
	"""
	Returns a structured hierarchy of folders and files for the Intranet Dashboard.
	"""
	try:
		# Get all team folders
		folders = frappe.get_all(
			"Enviro Team Folder",
			fields=["name", "folder_name", "is_system_folder"],
			order_by="folder_name asc",
		)

		folder_names = [f.name for f in folders]

		# Get all files attached to these folders
		files = []
		if folder_names:
			files = frappe.get_all(
				"File",
				filters={
					"attached_to_doctype": "Enviro Team Folder",
					"attached_to_name": ["in", folder_names],
				},
				fields=["name", "file_name", "file_url", "attached_to_name", "creation", "owner"],
				order_by="creation desc",
			)

		# Organize files into folders
		folder_data = []
		for folder in folders:
			folder_files = [f for f in files if f.attached_to_name == folder.name]
			# Convert full timestamp to nice date
			for ff in folder_files:
				ff.creation_date = frappe.utils.formatdate(ff.creation, "dd MMM YYYY")

			folder_data.append(
				{
					"name": folder.name,
					"folder_name": folder.folder_name,
					"is_system_folder": folder.is_system_folder,
					"files": folder_files,
					"file_count": len(folder_files),
				}
			)

		return folder_data
	except Exception:
		frappe.log_error(title="Intranet API Error", message=frappe.get_traceback())
		frappe.throw(_("Failed to fetch intranet data."))


@frappe.whitelist()
def create_folder(folder_name):
	"""
	Creates a new custom folder.
	"""
	try:
		if not folder_name:
			frappe.throw(_("Folder name is required."))

		if frappe.db.exists("Enviro Team Folder", folder_name):
			frappe.throw(_("A folder with this name already exists."))

		doc = frappe.new_doc("Enviro Team Folder")
		doc.folder_name = folder_name
		doc.is_system_folder = 0
		doc.insert(ignore_permissions=True)

		return doc.name
	except Exception as e:
		frappe.log_error(title="Intranet Folder Creation Error", message=frappe.get_traceback())
		frappe.throw(_(str(e)))
