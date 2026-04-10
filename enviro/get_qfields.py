import frappe


def execute():
	meta = frappe.get_meta("Quotation")
	for d in meta.fields:
		if d.fieldname in [
			"customer",
			"custom_site",
			"contact_person",
			"contact_display",
			"contact_mobile",
			"company",
		]:
			print(f"{d.fieldname} ({d.fieldtype}) - {d.label}")
