import frappe


def setup_hr_patches():
	"""
	Sets up server-side patches for HR logic.
	- Bypasses mandatory Leave Approver requirement.
	"""
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

	frappe.db.commit()


if __name__ == "__main__":
	setup_hr_patches()
