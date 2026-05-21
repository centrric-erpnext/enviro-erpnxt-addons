import frappe


def get_request_params():
	"""Helper to get parameters from form-data or JSON body"""
	params = frappe.form_dict.copy()
	if frappe.request.json:
		params.update(frappe.request.json)
	return params


@frappe.whitelist()
def get_current_employee():
	"""Returns the employee record linked to the current user"""
	return frappe.db.get_value(
		"Employee", {"user_id": frappe.session.user}, ["name", "employee_name", "image"], as_dict=True
	)


def save_signature(doctype, name, signature_b64):
	"""Saves a base64 signature as a File and returns the file_url"""
	import base64

	if "," in signature_b64:
		signature_b64 = signature_b64.split(",")[1]

	file_doc = frappe.new_doc("File")
	file_doc.file_name = f"signature_{name}.png"
	file_doc.is_private = 1
	file_doc.content = base64.b64decode(signature_b64)
	file_doc.attached_to_doctype = doctype
	file_doc.attached_to_name = name
	file_doc.insert(ignore_permissions=True)
	return file_doc.file_url
