import frappe


def run():
	print(
		[
			(f.fieldname, f.fieldtype, f.options, f.label)
			for f in frappe.get_meta("Quotation").fields
			if "party" in f.fieldname or "customer" in f.fieldname or "site" in f.fieldname
		]
	)
