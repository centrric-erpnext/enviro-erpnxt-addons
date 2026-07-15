import frappe


def run():
	print(
		"Checking Customer:",
		frappe.db.sql(
			'SELECT name FROM tabCustomer WHERE name="Temporary Client" or customer_name="Temporary Client"',
			as_dict=True,
		),
	)
	print(
		"Checking Lead:",
		frappe.db.sql(
			'SELECT name FROM tabLead WHERE name="Temporary Client" or lead_name="Temporary Client" or company_name="Temporary Client"',
			as_dict=True,
		),
	)
	print(
		"Checking Prospect:",
		frappe.db.sql(
			'SELECT name FROM tabProspect WHERE name="Temporary Client" or company_name="Temporary Client"',
			as_dict=True,
		),
	)
	print("Checking any Doctype:")
	print(frappe.db.sql("SELECT name FROM tabDocType WHERE name = 'Temporary Client'"))
