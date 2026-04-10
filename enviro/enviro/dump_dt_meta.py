import json

import frappe


@frappe.whitelist()
def dump_doctype(doctype_name):
	try:
		dt = frappe.get_doc("DocType", doctype_name)
		dt_dict = dt.as_dict()
		dt_dict["custom"] = 0
		return dt_dict
	except Exception as e:
		return {"error": str(e)}
