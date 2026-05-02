import frappe


def bypass_leave_approver():
	print("Creating Server Script to bypass Leave Approver requirement...")

	script_name = "Auto Set Leave Approver"
	if not frappe.db.exists("Server Script", script_name):
		ss = frappe.new_doc("Server Script")
		ss.name = script_name
		ss.script_type = "DocType Event"
		ss.reference_doctype = "Leave Application"
		ss.doctype_event = "before_save"
		ss.script = """
# Auto set leave approver to bypass mandatory check
if not doc.leave_approver:
    # Try to find an HR Manager or fallback to Administrator
    approver = frappe.db.get_value("UserPermission", {"allow": "Employee", "user": frappe.session.user}, "user")
    doc.leave_approver = approver or "Administrator"
"""
		ss.insert(ignore_permissions=True)
		print("Server Script created.")
	else:
		print("Server Script already exists.")

	# Update hr_dashboard.py API roles
	dashboard_api_path = "/home/midhul/frappe-bench/apps/enviro/enviro/enviro/api/hr_dashboard.py"
	with open(dashboard_api_path) as f:
		content = f.read()

	new_roles = 'allowed = ("Administrator", "Superadmin", "System Manager", "Manager", "HR Manager", "Accounts Manager", "Director")'
	if 'allowed = ("Administrator"' in content:
		import re

		content = re.sub(r"allowed = \(.*?\)", new_roles, content)
		with open(dashboard_api_path, "w") as f:
			f.write(content)
		print("Updated hr_dashboard.py with 'Director' role.")

	frappe.db.commit()
	print("All changes applied.")


if __name__ == "__main__":
	bypass_leave_approver()
