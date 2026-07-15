import frappe


def execute():
	if not frappe.db.exists("Customer", "Temporary Client"):
		doc = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Temporary Client",
				"customer_group": "Commercial",
				"territory": "Australia",
				"customer_type": "Company",
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
