import json

import frappe


def run():
	print(
		json.dumps(
			[
				{"fieldname": f.fieldname, "label": f.label, "allow_on_submit": f.allow_on_submit}
				for f in frappe.get_meta("Quotation").fields
				if f.fieldname == "company"
			]
		)
	)
	print(
		json.dumps(
			[
				{"fieldname": f.fieldname, "label": f.label, "allow_on_submit": f.allow_on_submit}
				for f in frappe.get_meta("Quotation").fields
				if f.label == "Company Name" or f.label == "Company"
			]
		)
	)
